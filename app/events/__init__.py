import json
import time
from flask import request
from flask_socketio import disconnect, emit, join_room, send
import redis
from app.events.classification_events import single_classification_finished_event
from app.extensions import socketio as sio
from app.schemas.classification_schemas import SingleClassificationResponse, validate_and_get_model
from app.core.logger_config import logger
from app.config import settings


def test_task(socket_session_id: str):
    # aqui simulamos uma tarefa longa
    for i in range(5):
        time.sleep(i)
        print(i)
    result = {"message": "Tarefa de teste foi executada com sucesso!"}
    sio.emit("finished_mock_task", result, to=socket_session_id)
    

@sio.on("connect")
def handle_connect():
    socket_session_id = request.sid
    print(f"✅ Cliente conectado: {socket_session_id}")
    print(sio.server.manager.rooms)
    sio.emit("connected", {"socket_session_id": socket_session_id}, to=socket_session_id)


@sio.on("ping_event")
def on_ping(data):
    socket_session_id = request.sid
    print(f"ping recebido de {socket_session_id}")
    sio.emit("pong_event", {"message": "pong"}, to=socket_session_id)


@sio.on("listen_to_updates")
def on_listen_to_updates(data):
    socket_session_id = request.sid
    for i in range(5):
        time.sleep(0.5)
        sio.emit("status_update", {"round": i+1, "total": 5}, to=socket_session_id)


@sio.on('message')
def handle_message(msg):
    print(f"Mensagem recebida: {msg}")
    send(f"Echo: {msg}")


@sio.on('custom_event')
def handle_custom_event(data):
    sid = request.sid
    print(f"Evento custom_event: {data}")
    time.sleep(5)
    emit("long_event", {"status": "ok", "data": data})
    disconnect(sid=sid)


@sio.on('join')
def handle_join(data):
    """
    Manipulador para clientes que desejam entrar em uma sala para
    receber notificações sobre um job específico.
    """
    room = data.get('room_id')
    if room:
        join_room(room)
        print(f"Cliente {request.sid} entrou na sala: {room}")


def redis_listener():
    print("📢 Ouvinte Redis iniciado, esperando por resultados de tarefas...")
    r = redis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('task_results')

    for message in pubsub.listen():
        logger.info(f"mensagem ouvida do canal redis: {message}")
        try:
            channel = message['channel'].decode('utf-8')
            data = json.loads(message['data'])

            if channel == 'task_results':
                room_id = data.pop('room_id')

                logger.info(f"[INTERCEPTADO]: Resultado para a sala {room_id}. Resultado: {data.get('result')}")

                payload = validate_and_get_model(data, SingleClassificationResponse)
                single_classification_finished_event(payload, room_id)

                sio.close_room(room_id)
        except Exception as e:
            logger.error(f"ERRO no ouvinte Redis: {e}")


