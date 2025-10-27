from app.schemas.model_schemas import ClassificationSchema
from app.services.partnumber_service import PartnumberService
from app.services.protocols import IClassificationService
from app.schemas.classification_schemas import StartBatchClassificationSchema, StartSingleClassificationSchema
from app.services.protocols import IAsyncTaskClient
from app.core.logger_config import logger

class ClassificationService(IClassificationService):
    def __init__(self, task_client:IAsyncTaskClient):
        self.task_client = task_client
        self.logger = logger
        self.partnumber_service = PartnumberService()

    def start_single_classification(self, schema:StartSingleClassificationSchema) -> dict:
        partnumber_classifications = self.partnumber_service.get_classifications(partnumber=schema.partnumber)

        if partnumber_classifications:
            partnumber_classifications = [ClassificationSchema.model_validate(c).model_dump(mode="json") for c in partnumber_classifications]

        message = "Seu pedido de classificação foi aceito e está sendo processado..."
        task_id = None

        if schema.reclassify or not partnumber_classifications:
            task_id = self.task_client.run_single_classification_task(schema)

        return {
            "message": message,
            "task_id": task_id,
            "classifications": partnumber_classifications
        }

    def start_batch_classification(self, schema: StartBatchClassificationSchema) -> dict:
        self.logger.info(f"Serviço para classificação de partnumbers: {schema.partnumbers}")
        existing_classifications = {}
        for p in schema.partnumbers:
            cl = self.partnumber_service.get_classifications(partnumber=p)
            if cl:
                cl = [ClassificationSchema.model_validate(c).model_dump(mode="json") for c in cl]
                existing_classifications[p] = cl

        task_id = self.task_client.run_batch_classification_task(schema)
        
        return {
            "message": "Seu pedido de classificação em lote foi recebido e está sendo processado.",
            "task_id": task_id,
            "classifications": existing_classifications
        }
