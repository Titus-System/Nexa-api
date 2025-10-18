import json
from typing import Any
from celery import Task
from celery.result import AsyncResult
from app.extensions import celery
from app.schemas.classification_schemas import StartBatchClassificationSchema, StartSingleClassificationSchema
from app.services.protocols import IAsyncTaskClient
from app.tasks.batch_classification_task_manager import BatchClassificationTaskManager
from app.tasks.single_classification_task_manager import SingleClassificationTaskManager


class AIClassificationClient(IAsyncTaskClient):
    def run_single_classification_task(self, task_data:StartSingleClassificationSchema):
        task: AsyncResult = ai_single_classification_task.delay(task_data.model_dump(exclude_none=True))
        return task.id
    
    def run_batch_classification_task(self, schema: StartBatchClassificationSchema):
        task: AsyncResult = ai_batch_classification_task.delay(schema.model_dump(exclude_none=True))
        return task.id


@celery.task(bind=True)
def ai_single_classification_task(self: Task, task_data:dict):
    classification_manager = SingleClassificationTaskManager(task_id=self.request.id, task_data=task_data)
    return classification_manager.run()


@celery.task(bind=True)
def ai_batch_classification_task(self:Task, task_data:dict):
    classification_manager = BatchClassificationTaskManager(task_id=self.request.id, task_data=task_data)
    return classification_manager.run()