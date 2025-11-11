import io
import pdfplumber
from flask import request
from flask_restful import Resource
from app.schemas.classification_schemas import StartBatchClassificationSchema
from app.services.classification_service import PartnumberClassificationService
from app.services.pdfExtrator import PdfParserFactory
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

        if file.filename == "" or file.filename is None:
            return {"message": "Arquivo sem nome."}, 400

        if not file.filename.lower().endswith(".pdf"):
            return {"message": "Formato inválido, apenas PDFs são aceitos."}, 400
        
        supplier = request.form.get("supplier")

        try:
            pdf_bytes = file.read()
            pdf_file = pdfplumber.open(io.BytesIO(pdf_bytes))

            extractor = PdfParserFactory(pdf_file, supplier)
            part_numbers = extractor.extract_partnumbers()

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
                "partnumbers": [i for i in part_numbers.keys()],
                "total_partnumbers": len(part_numbers)
            }, 202

        except Exception as e:
            return {"error": str(e)}, 500