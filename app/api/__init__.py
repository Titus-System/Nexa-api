from flask import Flask
from flask_restful import Api

from app.api.health_check import HealthCheck
    

def initialize_api(app: Flask) -> Api:
    api = Api(app)
    api.add_resource(HealthCheck, "/")

    return api
