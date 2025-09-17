import time
from flask import request
from flask_socketio import disconnect, emit, join_room, send
from app.extensions import socketio as sio


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