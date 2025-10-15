from app.schemas.model_schemas import ClassificationSchema
from app.services.partnumber_service import PartnumberService
from app.services.protocols import IClassificationService
from app.schemas.classification_schemas import StartSingleClassificationSchema
from app.services.protocols import IAsyncTaskClient


class ClassificationService(IClassificationService):
    def __init__(self, task_client:IAsyncTaskClient):
        self.task_client = task_client
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
