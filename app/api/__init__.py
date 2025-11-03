from flask import Flask
from flask_restful import Api

from app.api.classification_resource import BatchClassificationResource, SingleClassificationResource
from app.api.export_excel_resource import ExporExcelResource
from app.api.health_check import CheckWebSocketConnection, HealthCheck
from app.api.ncm_resource import NcmResource
from app.api.partnumber_resource import PartnumberResource
from app.api.task_resources import TaskResource
from app.api.upload_pdf_resource import UploadPedidoResource

    

def initialize_api(app: Flask) -> Api:
    api = Api(app)
    
    api.add_resource(HealthCheck, "/")
    api.add_resource(CheckWebSocketConnection, "/ws")
    api.add_resource(SingleClassificationResource, "/classify-partnumber")
    api.add_resource(TaskResource, "/tasks")
    api.add_resource(PartnumberResource, "/partnumbers", "/partnumbers/<string:partnumber>")
    api.add_resource(NcmResource, "/ncm", "/ncm/<string:ncm_code>")
    api.add_resource(UploadPedidoResource, "/upload-pdf")
    api.add_resource(BatchClassificationResource, "/classify-batch")
    api.add_resource(ExporExcelResource, "/export-excel")

    return api
