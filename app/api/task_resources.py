from flask import request
from flask_restful import Resource

from app.core.logger_config import logger
from app.schemas.model_schemas import ClassificationTaskSchema
from app.services.classification_tasks_service import ClassificationTaskService
from app.api.auth_helpers import get_current_user_id, jwt_required_optional


class TaskResource(Resource):
    def __init__(self):
        self.service = ClassificationTaskService()
        self.logger = logger

    @jwt_required_optional
    def get(self):
        self.logger.info(f"headers: {dict(request.headers)}")
        self.logger.info(f"args: {request.args.to_dict()}")
        self.logger.info(f"json: {request.get_json(silent=True)}")
        current_user_id = get_current_user_id()
        filters = {
            "task_id": request.args.get("task_id"),
            "job_id": request.args.get("job_id"),
            "progress_channel": request.args.get("progress_channel"),
            "status": request.args.get("status"),
            "user_id": current_user_id
        }
        # Always filter by current user's ID
        filters["user_id"] = current_user_id
        filters = {k:v for k, v in filters.items() if v is not None}
        tasks = self.filter_tasks(filters)
        return {"tasks": tasks}, 200
    
    def filter_tasks(self, filters: dict):
        tasks = self.service.get_tasks(filters)
        tasks = [ClassificationTaskSchema.model_validate(task).to_dict() for task in tasks]
        return tasks
    
    @jwt_required_optional
    def delete(self, task_id:str):
        current_user_id = get_current_user_id()
        # Verify the task belongs to the current user
        task = self.service.read(task_id)
        if not task:
            return {"error": "Task not found"}, 404
        if task.user_id != current_user_id:
            return {"error": "Unauthorized"}, 403
        task = self.service.delete(task_id)
        return {"message": "Task deleted successfully"}, 204

    
        