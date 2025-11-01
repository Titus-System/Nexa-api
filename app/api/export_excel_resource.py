from flask import Response, request
from flask_restful import Resource

from app.core.logger_config import logger
from app.schemas.model_schemas import ClassificationTaskSchema
from app.services.export_excel_service import ExportExcelService

class ExporExcelResource(Resource):
    def __init__(self):
        self.logger = logger
        self.service = ExportExcelService()

    def get(self):
        filters = {
            "classification_id": request.args.get("classification_id"),
            "task_id": request.args.get("task_id"),
        }

        filters = {k:v for k, v in filters.items() if v is not None}
        output = self.service.export_from_task_id(filters.get("task_id"))
        return Response (
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                "Content-Disposition": "attachment;filename=produtos_importacao.xlsx"
            }
        )
    