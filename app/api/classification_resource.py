from flask import request
from flask_restful import Resource
from pydantic import ValidationError
from dependency_injector.wiring import inject, Provide
import uuid

from app.containers import Container
from app.core.logger_config import logger
from app.schemas.classification_schemas import BatchClassificationRequest, SingleClassificationRequest, StartBatchClassificationSchema, StartSingleClassificationSchema
from app.schemas.model_schemas import ClassificationTaskSchema
from app.services.classification_table_service import ClassificationService
from app.services.protocols import IClassificationService


class BatchClassificationResource(Resource):
    @inject
    def __init__(
        self, 
        service: IClassificationService = Provide[Container.classification_service],
    ):
        self.service = service
        super().__init__()

    def post(self):
        try:
            body = BatchClassificationRequest(**request.get_json())
        except ValidationError as e:
            return {"errors": e.errors()}, 400
        
        room_id = str(uuid.uuid4())
        
        body = body.model_dump(exclude_none=True)
        body["room_id"] = room_id
        response = self.service.start_batch_classification(schema= StartBatchClassificationSchema(**body))
        
        print("Pedido de classificação foi recebido")
        return { 
            "message": response.get("message"), 
            "task_id": response.get("task_id"),
            "room_id": room_id,
            "classifications": response.get("classifications", [])
        }, 202


class SingleClassification(Resource):
    @inject
    def __init__(
        self, 
        service: IClassificationService = Provide[Container.classification_service],
    ):
        self.service = service
        super().__init__()


    def post(self):
        try:
            body = SingleClassificationRequest(**request.get_json())
        except ValidationError as e:
            return {"errors": e.errors()}, 400
        
        room_id = str(uuid.uuid4())
        
        body = body.model_dump(exclude_none=True)
        body["room_id"] = room_id
        body["partnumber"] = body["partnumber"].strip().upper()
        response = self.service.start_single_classification(schema= StartSingleClassificationSchema(**body))
        
        print("Pedido de classificação foi recebido")
        return { 
            "message": response.get("message"), 
            "task_id": response.get("task_id"),
            "room_id": room_id,
            "classifications": response.get("classifications", [])
        }, 202
    

class ClassificationResource(Resource):
    def __init__(self):
        self.service = ClassificationService()
        self.logger = logger

    def get(self):
        filters = {
            "classification_id": request.args.get("classification_id"),
            "job_id": request.args.get("job_id"),
            "progress_channel": request.args.get("progress_channel"),
            "status": request.args.get("status"),
            "user_id": request.args.get("user_id")
        }
        filters = {k:v for k, v in filters.items() if v is not None}
        tasks = self.filter_tasks(filters)
        return {"tasks": tasks}, 200
    
    def filter_tasks(self, filters: dict):
        tasks = self.service.get_classifications(filters)
        tasks = [ClassificationTaskSchema.model_validate(task).to_dict() for task in tasks]
        return tasks