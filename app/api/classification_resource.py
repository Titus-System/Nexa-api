from flask import request
from flask_restful import Resource
from pydantic import ValidationError
from dependency_injector.wiring import inject, Provide
import uuid

from app.containers import Container
from app.core.logger_config import logger
from app.schemas.classification_schemas import SingleClassificationRequest, StartSingleClassificationSchema
from app.services.protocols import IClassificationService


class PartnumberClassification(Resource):
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