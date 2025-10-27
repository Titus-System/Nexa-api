from flask import request
from flask_restful import Resource

from app.core.logger_config import logger
from app.schemas.model_schemas import ClassificationTaskSchema
from app.services.classification_tasks_service import ClassificationTaskService


class TaskResource(Resource):
    def __init__(self):
        self.service = ClassificationTaskService()
        self.logger = logger

    def get(self):
        filters = {
            "task_id": request.args.get("task_id"),
            "job_id": request.args.get("job_id"),
            "progress_channel": request.args.get("progress_channel"),
            "status": request.args.get("status"),
            "user_id": request.args.get("user_id")
        }
        filters = {k:v for k, v in filters.items() if v is not None}
        tasks = self.filter_tasks(filters)
        return {"tasks": tasks}, 200
    
    def filter_tasks(self, filters: dict):
        tasks = self.service.get_tasks(filters)
        tasks = [ClassificationTaskSchema.model_validate(task).to_dict() for task in tasks]
        return tasks
    
        