from flask import Response, json, request
from flask_restful import Resource
from app.config import settings


class HealthCheck(Resource):
    def get(self):
        return Response(
            json.dumps(
                {
                    'resposta': f"{settings.APP_NAME} backend está rodando."
                }, 
                ensure_ascii=False
            ),
            content_type = 'application/json; charset=utf-8',
            status = 200
        )
