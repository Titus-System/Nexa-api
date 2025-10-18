import json
from typing import Dict
import uuid
import requests
from app.events.events_enum import EventName, RedisChannelName
from app.models.models import TaskStatus
from app.schemas.ai_schemas import AIBatchClassificationRequest, AISingleClassificationRequest
from app.schemas.classification_schemas import FailedStatusResponse, SingleClassification, SingleClassificationResponse, UpdateStatusResponse, validate_and_get_model
from app.services.classification_table_service import ClassificationService
from app.services.classification_tasks_service import ClassificationTaskService
from app.services.manufacturers_service import ManufacturersService
from app.services.partnumber_service import PartnumberService
from app.services.tipi_service import TipiService
from . import external_socketio, celery_logger, redis_client
from app.config import settings


class BatchClassificationTaskManager:
    def __init__(self, task_id:str, task_data:Dict):
        self.task_id = task_id
        self.task_data = task_data

        self.room_id:str = self.task_data.pop("room_id")
        self.user_id: str = self.task_data.get("user_id")
        self.partnumbers:list[str] = self.task_data.get("partnumbers")

        self.progress_channel = f"progress-{uuid.uuid4()}"

        self.logger = celery_logger
        self.socket = external_socketio
        self.redis_client = redis_client
        
        self.task_service = ClassificationTaskService()
        self.classification_service = ClassificationService()
        self.partnumber_service = PartnumberService()
        self.tipi_service = TipiService()
        self.manufaturer_service = ManufacturersService()

    
    def run(self):
        self._create_task_in_db()
        try:
            pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(self.progress_channel)

            job_id = self._initiate_remote_job()
            if not job_id:
                pubsub.unsubscribe(self.progress_channel)
                self.task_service.mark_as_failed(self.task_id, "Falha ao iniciar o job de classificação em Nexa IA.")
                return
            
            self.task_service.update(self.task_id, {"job_id":job_id})
            self._listen_for_progress(pubsub)

        finally:
            if pubsub: 
                pubsub.unsubscribe(self.progress_channel)

    def _create_task_in_db(self):
        self.task_service.create(
            self.task_id,
            self.room_id,
            self.progress_channel,
            user_id=self.user_id
        )
        for partnumber in self.partnumbers:
            self.partnumber_service.create(partnumber)

    def _initiate_remote_job(self):
        request_data = AIBatchClassificationRequest(
            **self.task_data,
            progress_channel=self.progress_channel
        )
        try:
            response = requests.post(
                f"{settings.NEXA_AI_SERVER}/process/batch_partnumbers",
                json = request_data.model_dump()
            )
            self.logger.info(f"Requisição POST enviada para {settings.NEXA_AI_SERVER}/process/batch_partnumbers. Status code: {response.status_code}")
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
            self.task_service.mark_as_failed(self.task_id, "Erro ao iniciar job em Nexa AI.")
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
        elif status == "partial_result":
            self._handle_partial_result(data)
            return False
        elif status == "failed":
            self._handle_failed_status(data)
            return False

    def _handle_done_status(self, data):
        payload = {
            "status": TaskStatus.DONE.value,
            "message": "Processamento de múltiplos partnumbers concluído com sucesso.",
            "result": data.get("result", {}),
            "partnumbers": self.partnumbers,
            "room_id": self.room_id
        }
        self.task_service.mark_as_finished(self.task_id, {"status": payload["status"], "message": payload["message"]})
        self.logger.info(f"Marked task {self.task_id} as finished.")
        
        self.redis_client.publish(
            RedisChannelName.BATCH_TASK_DONE.value, 
            json.dumps(payload)
        )
        return True

    def _handle_partial_result(self, data:dict):
        # atualizar status da task
        partial_result = data.get('partial_result', {})
        self.logger.info(f"\n[RESULTADO PARCIAL] Resultado parcial recebido: {partial_result}\n")
        self.task_service.update_status(
            task_id = self.task_id,
            status = TaskStatus.PROCESSING.value,
            current = data.get("current"),
            total = data.get("total"),
            message = data.get("message")
        )

        # salvar classificação do partnumber
        single_classification = data.get("single_classification")
        if not single_classification:
            self.logger.error("Erro ao processar resultado parcial. Resultado de single_classification não encontrado.")
            return

        single_classification = validate_and_get_model(single_classification, SingleClassification)

        tipi = self.tipi_service.find_from_ncm_ex(single_classification.ncm, single_classification.exception)
        try:
            manufacturer = self.manufaturer_service.find_or_create(single_classification.fabricante, single_classification.endereco, single_classification.pais)
        except Exception as e:
            self.logger.info(f"Erro ao lidar com fabricante {single_classification.fabricante}: {e}")
            manufacturer = None

        create_classification_dto = {
            "partnumber": single_classification.partnumber,
            "classification_task_id": self.task_id,
            "tipi_id": tipi.id if tipi else None,
            "manufacturer_id": manufacturer.id if manufacturer else None,
            "short_description": None,
            "long_description": single_classification.description,
            "confidence_rate": single_classification.confidence_score,
            "user_id": self.user_id
        }
        self.classification_service.create(create_classification_dto)

        # emitir evento classification_update_status
        progress_payload = {
            "status": TaskStatus.PROCESSING.value,
            "current": data.get("current"),
            "total": data.get("total"),
            "message": data.get("message")
        }
        progress_payload = validate_and_get_model(progress_payload, UpdateStatusResponse).model_dump(exclude_none=True)

        self.socket.emit(
            EventName.CLASSIFICATION_UPDATE_STATUS.value,
            progress_payload,
            to=self.room_id
        )
        
        return False


    def _handle_processing_status(self, data):
        progress_payload = data.get('progress', {})
        self.logger.info(f"\n[PROGRESS] Progresso recebido: {progress_payload}\n")
        progress_payload['status'] = TaskStatus.PROCESSING.value
        progress_payload = validate_and_get_model(progress_payload, UpdateStatusResponse).model_dump(exclude_none=True)
        self.task_service.update_status(
            task_id = self.task_id,
            status = TaskStatus.PROCESSING.value,
            current = progress_payload.get("current"),
            total=progress_payload.get("total"),
            message = progress_payload.get("message")
        )
        self.socket.emit(
            EventName.CLASSIFICATION_UPDATE_STATUS.value,
            progress_payload,
            to=self.room_id
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