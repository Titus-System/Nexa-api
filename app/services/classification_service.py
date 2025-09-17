from celery.result import AsyncResult
from app.services.protocols import IClassificationService
from app.schemas.classification_schemas import StartClassificationSchema
from app.services.protocols import IAsyncTaskClient


class ClassificationService(IClassificationService):
    def __init__(self, task_client:IAsyncTaskClient):
        self.task_client = task_client

    def start_classification(self, schema:StartClassificationSchema) -> str:
        task_data = {"partnumber": schema.partnumber}

        task_id = self.task_client.run_task(schema.model_dump(exclude_none=True))

        return task_id
    

