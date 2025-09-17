from flask import request
from flask_restful import Resource
from pydantic import ValidationError
from dependency_injector.wiring import inject, Provide
import uuid

from app.containers import Container
from app.core.logger_config import logger
from app.schemas.classification_schemas import ClassificationRequest, StartClassificationSchema
from app.services.protocols import IClassificationService


class ClassificationResource(Resource):
    @inject
    def __init__(
        self, 
        service: IClassificationService = Provide[Container.classification_service],
    ):
        self.service = service
        super().__init__()


    def post(self):
        try:
            body = ClassificationRequest(**request.get_json())
        except ValidationError as e:
            return {"errors": e.errors()}, 400
        
        room_id = str(uuid.uuid4())
        
        body = body.model_dump()
        body["room_id"] = room_id
        task_id = self.service.start_classification(schema= StartClassificationSchema(**body))
        
        print("Pedido de classificação foi recebido")
        return { 
            "message": "Seu pedido de classificação foi aceito...", 
            "task_id": task_id,
            "room_id": room_id
        }, 202
    
    