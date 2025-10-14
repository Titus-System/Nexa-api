import json
from typing import Dict
import uuid
import requests
from app.events.events_enum import EventName, RedisChannelName
from app.models.models import TaskStatus
from app.schemas.ai_schemas import AISingleClassificationRequest
from app.schemas.classification_schemas import FailedStatusResponse, UpdateStatusResponse, validate_and_get_model
from app.services.classification_tasks_service import ClassificationTaskService
from . import external_socketio, celery_logger, redis_client
from app.config import settings


class SingleClassificationTaskManager:
    def __init__(self, task_id:str, task_data:Dict):
        self.task_id = task_id
        self.task_data = task_data

        self.room_id = self.task_data.pop("room_id")
        self.user_id = self.task_data.get("user_id")
        self.partnumber = self.task_data.get("partnumber")

        self.progress_channel = f"progress-{uuid.uuid4()}"

        self.logger = celery_logger
        self.socket = external_socketio
        self.db_service = ClassificationTaskService()
        self.redis_client = redis_client

    def run(self):
        self._create_task_in_db()
        pubsub = None
        try:
            pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(self.progress_channel)

            job_id = self._initiate_remote_job()
            if not job_id:
                pubsub.unsubscribe(self.progress_channel)
                self.db_service.mark_as_failed(self.task_id, "Falha ao iniciar o job de classificação em Nexa IA.")
                return
            
            self.db_service.update(self.task_id, {"job_id":job_id})
            self._listen_for_progress(pubsub)

        finally:
            if pubsub: 
                pubsub.unsubscribe(self.progress_channel)

    def _create_task_in_db(self):
        self.db_service.create(
            self.task_id,
            self.room_id,
            self.progress_channel,
            user_id=None
        )
    
    def _initiate_remote_job(self):
        request_data = AISingleClassificationRequest(
            **self.task_data,
            progress_channel=self.progress_channel
        )
        try:
            response = requests.post(
                f"{settings.NEXA_AI_SERVER}/process/single_partnumber",
                json = request_data.model_dump()
            )
            self.logger.info(f"Requisição POST enviada para {settings.NEXA_AI_SERVER}/process_single_partnumber. Status code: {response.status_code}")
            response.raise_for_status()
            job_id = response.json()['job_id']
            self.logger.info(f"Iniciado job de processamento externo com ID: {job_id}")
            return job_id
        except requests.RequestException as e:
            self.logger.error("Falha ao iniciar job em Nexa AI")
            error_payload = FailedStatusResponse(
                status=TaskStatus.FAILED.value,
                message="Erro inesperado em Nexa AI ao iniciar processamento do partnumber."
            )
            self.socket.emit(
                EventName.CLASSIFICATION_UPDATE_STATUS.value,
                error_payload,
                to=self.room_id
            )

    def _listen_for_progress(self, pubsub):
        for message in pubsub.listen():
            try:
                data = json.loads(message['data'])
                status = data.get("status")
                
                if self._handle_message(status, data):
                    break

            except (json.JSONDecodeError, TypeError) as e:
                celery_logger.warning(f"Erro ao processar mensagem do Redis: {e}")
        return None

    def _handle_message(self, status, data):
        if status == "done":
            self._handle_done_status(data)
            return True
        elif status == "processing":
            self._handle_processing_status(data)
            return False
        elif status == "failed":
            self._handle_failed_status(data)
            return False

    def _handle_done_status(self, data):
        payload = {
            "status": TaskStatus.DONE.value,
            "message": "Processamento consluído com sucesso.",
            "result": data.get("result", {}),
            "partnumber": self.partnumber,
            "room_id": self.room_id
        }
        self.redis_client.publish(
            RedisChannelName.TASK_RESULTS.value, 
            json.dumps(payload)
        )
        return True
    
    def _handle_processing_status(self, data):
        progress_payload = data.get('progress', {})
        self.logger.info(f"\n[PROGRESS] Progresso recebido: {progress_payload}\n")
        progress_payload['status'] = TaskStatus.PROCESSING.value
        progress_payload = validate_and_get_model(progress_payload, UpdateStatusResponse).model_dump(exclude_none=True)
        self.socket.emit(
            EventName.CLASSIFICATION_UPDATE_STATUS.value,
            progress_payload
        )
        self.redis_client.publish(
            'task_progress', 
            json.dumps(progress_payload)
        )
        return False
    
    def _handle_failed_status(self, data):
        fail_payload = {
            "status": TaskStatus.FAILED.value,
            "message": data.get('error', 'O processamento falhou sem mensagem de erro.')
        }
        fail_payload = validate_and_get_model(fail_payload, FailedStatusResponse).model_dump(exclude_none=True)
        external_socketio.emit(
            EventName.CLASSIFICATION_UPDATE_STATUS.value,
            fail_payload,
            to=self.room_id
        )
        return False
        