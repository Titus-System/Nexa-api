import json
from app.events.events_enum import EventName
from app.models.models import TaskStatus
from app.schemas.classification_schemas import FailedStatusResponse, SingleClassification, UpdateStatusResponse, validate_and_get_model
from app.services.classification_table_service import ClassificationService
from app.services.classification_tasks_service import ClassificationTaskService
from app.services.manufacturers_service import ManufacturersService
from app.services.partnumber_service import PartnumberService
from app.services.tipi_service import TipiService
from . import external_socketio, celery_logger, redis_client


class ProgressListener:
    def __init__(self, pubsub, task_id, room_id, partnumbers, user_id):
        self.pubsub = pubsub
        self.task_id = task_id
        self.room_id = room_id
        self.partnumbers = partnumbers
        self.user_id = user_id

        self.logger = celery_logger
        self.socket = external_socketio
        self.redis_client = redis_client
        
        self.task_service = ClassificationTaskService()
        self.classification_service = ClassificationService()
        self.partnumber_service = PartnumberService()
        self.tipi_service = TipiService()
        self.manufaturer_service = ManufacturersService()

    def listen_for_progress(self):
        for message in self.pubsub.listen():
            try:
                data = json.loads(message['data'])
                status = data.get("status")
                
                if self._handle_message(status, data):
                    self.logger.info(f"\n[LISTEN] mensagem ouvida no redis: {data}")
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
        return None

    def _handle_done_status(self, data):
        payload = {
            "status": TaskStatus.DONE.value,
            "message": "Processamento de múltiplos partnumbers concluído com sucesso.",
            "result": data.get("result", {}),
            "partnumbers": self.partnumbers,
            "room_id": self.room_id,
            "task_id": self.task_id
        }
        self.task_service.mark_as_finished(self.task_id, {"status": payload["status"], "message": payload["message"]})
        self.logger.info(f"Marked task {self.task_id} as finished.")

        import time
        try:
            self.logger.info("[TIRA_TEIMA] Antes do emit final.")
            self.socket.emit(EventName.BATCH_CLASSIFICATION_FINISHED.value, payload, to=self.room_id)
            self.logger.info(f"[TIRA_TEIMA] Depois do emit final: {payload}")
        except Exception as e:
            self.logger.exception(f"Erro ao emitir evento final: {e}")
        finally:
            time.sleep(1)
        return True

    def _handle_partial_result(self, data:dict):
        # atualizar status da task
        self.logger.info(f"\n[RESULTADO PARCIAL] Resultado parcial recebido: {data}\n")
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
            return None

        single_classification = validate_and_get_model(single_classification, SingleClassification)

        pre_classification = self.classification_service.get_by_taskid_and_partnumber(self.task_id, single_classification.partnumber)
        
        tipi = self.tipi_service.find_from_ncm_ex(single_classification.ncm, single_classification.exception)
        
        manufacturer_id = pre_classification.manufacturer_id

        if not manufacturer_id:
            manufacturer = self.manufaturer_service.find_or_create(
                single_classification.fabricante,
                single_classification.endereco,
                single_classification.pais
            )
            manufacturer_id = manufacturer.id

        address =  pre_classification.address

        if address is None and single_classification.endereco is not None:
            address = single_classification.endereco

        update_attr = {
            "tipi_id": tipi.id if tipi else None,
            "manufacturer_id": manufacturer_id if manufacturer_id else None,
            "long_description": single_classification.description,
            "address": address,
            "confidence_rate": single_classification.confidence_score,
        }

        self.classification_service.update(pre_classification.id, update_attr)

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
    