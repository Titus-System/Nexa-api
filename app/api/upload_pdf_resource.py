from flask import request
from flask_restful import Resource
from app.schemas.classification_schemas import StartBatchClassificationSchema
from app.services.classification_service import PartnumberClassificationService
from app.services.pdfExtrator import extract_part_numbers
from app.core.logger_config import logger

from flask import request
from flask_restful import Resource
import uuid



class UploadPedidoResource(Resource):
    def __init__(self):
        self.service = PartnumberClassificationService()
        self.logger = logger


    def post(self):
        if "pedido" not in request.files:
            return {"message": "Nenhum arquivo enviado."}, 400

        file = request.files["pedido"]

        if file.filename == "":
            return {"message": "Arquivo sem nome."}, 400

        if not file.filename.lower().endswith(".pdf"):
            return {"message": "Formato inválido, apenas PDFs são aceitos."}, 400

        try:
            pdf_bytes = file.read()
            part_numbers = extract_part_numbers(pdf_bytes)

            room_id = str(uuid.uuid4())

            schema = StartBatchClassificationSchema(
                partnumbers=part_numbers,
                room_id=room_id,
                reclassify=request.form.get("reclassify", "false").lower() == "true",
                user_id=int(request.form.get("user_id", 1))
            )

            response = self.service.start_batch_classification(schema)
            
            self.logger.info("Pedido de classificação em pdf foi recebido")

            return { 
                "message": "PDF recebido e processado com sucesso! Partnumbers extraídos estão sendo classificados.",
                "task_id": response.get("task_id"),
                "room_id": room_id,
                "classifications": response.get("classifications", []),
                "partnumbers": part_numbers,
                "total_partnumbers": len(part_numbers)
            }, 202

        except Exception as e:
            return {"error": str(e)}, 500