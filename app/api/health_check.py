from http.client import HTTPException
import time
from flask import Response, json, request
from flask_restful import Resource
from app.config import settings
from app.events import test_task
from app.extensions import socketio


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

        sid = body.get('socket_session_id')
        if not sid:
            return {
                "error": "BadRequest - sid não informado no corpo da requisição"
            }, 400

        ## TODO: implementar check se existe conexão ativa com sid fornecido
        
        socketio.start_background_task(test_task, sid)
        
        return { 
            "message": "Conexão websocket ativa e saudável.",
            "socket_session_id": sid
        }, 202
