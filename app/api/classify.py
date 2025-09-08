from typing import Optional
import uuid
from flask import request
from flask_restful import Resource
from pydantic import BaseModel, ValidationError

# Em um arquivo como app/auth/schemas.py ou um novo app/classification/schemas.py

from pydantic import BaseModel, Field


class ClassificationRequest(BaseModel):
    partnumber: str = Field(..., min_length=3, description="O partnumber do produto a ser classificado.")
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    socket_session_id: str = Field(..., description="O ID da sessão do cliente no Socket.IO para retorno da notificação.")


class PartNumberResource(Resource):
    def post(self):
        data = request.get_json()
        print("request json: ", data)
        try:
            valid = ClassificationRequest(**data)
        except ValidationError as e:
            return {"error": e.errors()}, 400
        
        # task = run_partnumber_research_task(
        #     partnumber=valid.partnumber,
        #     socket_session_id = valid.socket_session_id
        # )

        
        return { 
            "message": "Seu pedido foi aceito...", 
            # "task_id": task
        }, 202