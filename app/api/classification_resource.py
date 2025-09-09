from flask import request
from flask_restful import Resource
from pydantic import ValidationError
from app.core.logger_config import logger
from app.schemas.classification_schemas import ClassificationRequest
from app.services.protocols import ClassificationServiceProtocol


class ClassificationResource(Resource):
    service_class: ClassificationServiceProtocol = None

    def post(self):
        try:
            body = ClassificationRequest(**request.get_json())
        except ValidationError as e:
            return {"errors": e.errors()}, 400
        
        task_id = self.service_class.start_classification(schema=body)
        
        print("Pedido de classificação foi recebido")
        return { 
            "message": "Seu pedido de classificação foi aceito...", 
            "task_id": task_id
        }, 202
    
    