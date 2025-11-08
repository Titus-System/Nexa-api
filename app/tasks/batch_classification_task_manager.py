from typing import Dict
import uuid
import requests
from app.events.events_enum import EventName
from app.models.models import TaskStatus
from app.pdf_parsers.protocols import PartnumberInfo
from app.schemas.ai_schemas import AIBatchClassificationRequest
from app.schemas.classification_schemas import FailedStatusResponse, StartBatchClassificationSchema
from app.services.classification_table_service import ClassificationService
from app.services.classification_tasks_service import ClassificationTaskService
from app.services.manufacturers_service import ManufacturersService
from app.services.ncm_service import NcmService
from app.services.partnumber_service import PartnumberService
from app.services.tipi_service import TipiService
from app.tasks.progress_listener import ProgressListener
from . import external_socketio, celery_logger, redis_client
from app.config import settings


class BatchClassificationTaskManager:
    def __init__(self, task_id:str, task_data:StartBatchClassificationSchema):
        self.task_id = task_id
        self.task_data = task_data

        self.room_id = self.task_data.room_id
        self.user_id = self.task_data.user_id or 1
        self.partnumbers = self.task_data.partnumbers

        self.progress_channel = f"progress-{uuid.uuid4()}"

        self.logger = celery_logger
        self.socket = external_socketio
        self.redis_client = redis_client
        
        self.task_service = ClassificationTaskService()
        self.classification_service = ClassificationService()
        self.partnumber_service = PartnumberService()
        self.tipi_service = TipiService()
        self.manufaturer_service = ManufacturersService()
        self.ncm_service = NcmService()

    
    def run(self):
        self.logger.info(f"\n[INICIANDO] Iniciando processamento em lote...\n")
        self._create_task_in_db()
        pubsub = None
        try:
            job_id = self._initiate_remote_job()
            if not job_id:
                self.task_service.mark_as_failed(self.task_id, "Falha ao iniciar o job de classificação em Nexa IA.")
                return
            
            pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(self.progress_channel)

            self.task_service.update(self.task_id, {"job_id":job_id})
            ProgressListener(
                pubsub, self.task_id, self.room_id, [i for i in self.partnumbers.keys()], self.user_id
            ).listen_for_progress()

        finally:
            if pubsub:
                self.logger.info(f"Desinscrevendo worker do canal {self.progress_channel} do Redis")
                pubsub.unsubscribe(self.progress_channel)


    def _create_task_in_db(self):
        self.task_service.create(
            self.task_id,
            self.room_id,
            self.progress_channel,
            user_id=self.user_id
        )
        for partnumber, info in self.partnumbers.items():
            self.logger.info(f"Iniciando o registro de classificação prévia: {info}")
            self.partnumber_service.create(partnumber)
            mnf = None
            ncm = None
            tipi = None
            if info.manufacturer:
                mnf = self.manufaturer_service.find_or_create(info.manufacturer)
            if info.ncm:
                ncm = self.ncm_service.create(info.ncm)
                tipi = self.tipi_service.create({"ncm_code":ncm.code})

            self.classification_service.create({
                "partnumber": info.partnumber,
                "classification_task_id": self.task_id,
                "manufacturer_id": mnf.id if mnf else None,
                "short_description": info.erp_description,
                "confidence_rate": 0.98,
                "user_id": self.user_id,
                "tipi_id": tipi.id if tipi else None,
                "country_code": info.coo
            })


    def _initiate_remote_job(self):
        request_data = AIBatchClassificationRequest(
            partnumbers = self.partnumbers,
            progress_channel = self.progress_channel
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
            self.logger.error(f"Falha ao iniciar job em Nexa AI: {str(e)}")
            error_payload = FailedStatusResponse(
                status=TaskStatus.FAILED,
                message="Erro inesperado em Nexa AI ao iniciar processamento do partnumber."
            ).model_dump()
            self.task_service.mark_as_failed(self.task_id, "Erro ao iniciar job em Nexa AI.")
            self.socket.emit(
                EventName.CLASSIFICATION_UPDATE_STATUS.value,
                error_payload,
                to=self.room_id
            )
