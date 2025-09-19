from flask import Flask
from flask_restful import Api

from app.api.classification_resource import PartnumberClassification
from app.api.health_check import CheckWebSocketConnection, HealthCheck
    

def initialize_api(app: Flask) -> Api:
    api = Api(app)
    
    api.add_resource(HealthCheck, "/")
    api.add_resource(CheckWebSocketConnection, "/ws")
    api.add_resource(PartnumberClassification, "/classify-partnumber")

    return api
