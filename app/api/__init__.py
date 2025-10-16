from flask import Flask
from flask_restful import Api

from app.api.classification_resource import PartnumberClassification
from app.api.health_check import CheckWebSocketConnection, HealthCheck
from app.api.partnumber_resource import PartnumberResource
from app.api.task_resources import TaskResource
from app.api.upload_pdf_resource import UploadPedidoResource

    

def initialize_api(app: Flask) -> Api:
    api = Api(app)
    
    api.add_resource(HealthCheck, "/")
    api.add_resource(CheckWebSocketConnection, "/ws")
    api.add_resource(PartnumberClassification, "/classify-partnumber")
    api.add_resource(TaskResource, "/tasks")
    api.add_resource(PartnumberResource, "/partnumbers", "/partnumbers/<string:partnumber>")
    api.add_resource(UploadPedidoResource, "/upload-pdf")


    return api
