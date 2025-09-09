from flask import Flask
from flask_restful import Api

from app.api.classification_resource import ClassificationResource
from app.api.health_check import CheckWebSocketConnection, HealthCheck
from app.services.classification_service import ClassificationService
    

def initialize_api(app: Flask) -> Api:
    api = Api(app)
    
    api.add_resource(HealthCheck, "/")
    api.add_resource(CheckWebSocketConnection, "/ws")

    ClassificationResource.service_class=ClassificationService
    api.add_resource(ClassificationResource, "/classify")

    return api
