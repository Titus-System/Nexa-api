import time
from flask import request
from flask_socketio import emit, send
from app.extensions import socketio as sio


def mock_task(sid: str):
    # aqui simulamos uma tarefa longa
    for i in range(5):
        time.sleep(i)
        print(i)
    result = {"message": "Tarefa de teste foi executada com sucesso!"}
    sio.emit("finished_mock_task", result, to=sid)
    

@sio.on("connect")
def handle_connect():
    sid = request.sid
    print(f"✅ Cliente conectado: {sid}")
    sio.emit("connected", {"sid": sid}, to=sid)


@sio.on("ping_event")
def on_ping(data):
    sid = data.get('sid', None)
    print(f"ping recebido de {sid}")
    time.sleep(2)
    sio.emit("pong_event", {"message": "pong"}, to=sid)


@sio.on("listen_to_updates")
def on_listen_to_updates(data):
    sid = data.get('sid', None)
    for i in range(5):
        time.sleep(i)
        sio.emit("status_update", {"round": i+1, "total": 5}, to=sid)


@sio.on('message')
def handle_message(msg):
    print(f"Mensagem recebida: {msg}")
    send(f"Echo: {msg}")


@sio.on('custom_event')
def handle_custom_event(data):
    print(f"Evento custom_event: {data}")
    time.sleep(10)
    emit("long_event", {"status": "ok", "data": data})


