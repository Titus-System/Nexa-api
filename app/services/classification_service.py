from celery.result import AsyncResult
from app.services.partnumber_service import PartnumberService
from app.services.protocols import IClassificationService
from app.schemas.classification_schemas import StartSingleClassificationSchema
from app.services.protocols import IAsyncTaskClient


class ClassificationService(IClassificationService):
    def __init__(self, task_client:IAsyncTaskClient):
        self.task_client = task_client
        self.partnumber_service = PartnumberService()

    def start_single_classification(self, schema:StartSingleClassificationSchema) -> dict:
        if not schema.reclassify:
            partnumber_classifications = self.partnumber_service.get_classifications(partnumber=schema.partnumber)
            print("Classificações existentes para o partnumber:", partnumber_classifications)
            if partnumber_classifications: 
                return {
                    "message": "Partnumber já classificado.",
                    "task_id": None,
                    "classifications": [c for c in partnumber_classifications]
                }

        task_id = self.task_client.run_single_classification_task(schema)

        return {
            "message": "Seu pedido de classificação foi aceito e está sendo processado...",
            "task_id": task_id,
            "classifications": []
        }