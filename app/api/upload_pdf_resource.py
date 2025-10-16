from flask import request
from flask_restful import Resource
from app.services.pdfExtrator import extract_part_numbers


class UploadPedidoResource(Resource):
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

            return {
                "message": "Arquivo processado com sucesso!",
                "part_numbers": part_numbers,
                "total": len(part_numbers)
            }, 200

        except Exception as e:
            return {"error": str(e)}, 500