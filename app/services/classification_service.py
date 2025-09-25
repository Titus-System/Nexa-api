from celery.result import AsyncResult
from app.services.protocols import IClassificationService
from app.schemas.classification_schemas import StartSingleClassificationSchema
from app.services.protocols import IAsyncTaskClient


class ClassificationService(IClassificationService):
    def __init__(self, task_client:IAsyncTaskClient):
        self.task_client = task_client

    def start_single_classification(self, schema:StartSingleClassificationSchema) -> str:

        task_id = self.task_client.run_single_classification_task(schema)

        return task_id