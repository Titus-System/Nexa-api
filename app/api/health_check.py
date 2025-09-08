from http.client import HTTPException
import time
from flask import Response, json, request
from flask_restful import Resource
from app.config import settings
from app.events import mock_task


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


class CheckWebSocketConnection(Resource):
    def post(self):
        body = request.get_json()
        print("body request json: ", body)

        sid = body.get('sid')
        if not sid:
            return {
                "error": "BadRequest - sid não informado no corpo da requisição"
            }, 400
        from app.extensions import socketio
        socketio.start_background_task(mock_task, sid)
        
        return { 
            "message": "Seu pedido foi aceito...", 
            # "task_id": task
        }, 202
