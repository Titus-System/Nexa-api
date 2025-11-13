from flask import Flask
from flask_restful import Api

from app.api.classification_resource import BatchClassificationResource, SingleClassificationResource
from app.api.export_excel_resource import ExporExcelResource
from app.api.health_check import CheckWebSocketConnection, HealthCheck
from app.api.ncm_resource import NcmResource
from app.api.partnumber_resource import PartnumberResource
from app.api.task_resources import TaskResource
from app.api.upload_pdf_resource import UploadPedidoResource
from app.api.auth_routes import RegisterResource, LoginResource

    

def initialize_api(app: Flask) -> Api:
    api = Api(app)
    
    # Authentication routes (no JWT required)
    api.add_resource(RegisterResource, "/register")
    api.add_resource(LoginResource, "/login")
    
    # Health check (no JWT required)
    api.add_resource(HealthCheck, "/")
    api.add_resource(CheckWebSocketConnection, "/ws")
    
    # Protected routes (JWT required)
    api.add_resource(SingleClassificationResource, "/classify-partnumber")
    api.add_resource(TaskResource, "/tasks", "/tasks/<string:task_id>")
    api.add_resource(PartnumberResource, "/partnumbers", "/partnumbers/<string:partnumber>")
    api.add_resource(NcmResource, "/ncm", "/ncm/<string:ncm_code>")
    api.add_resource(UploadPedidoResource, "/upload-pdf")
    api.add_resource(BatchClassificationResource, "/classify-batch")
    api.add_resource(ExporExcelResource, "/export-excel")

    return api
