import socketio

# Conexão com o servidor de teste
sio_client = socketio.Client()

received_events = {}


@sio_client.on("connected")
def on_connected(data):
    received_events["connected"] = data


@sio_client.on("disconnect")
def on_disconnected():
    received_events["disconnect"] = True


@sio_client.event
def disconnected():
    received_events["disconnected"] = {}


@sio_client.on("pong_event")
def on_pong(data):
    received_events["pong"] = data


@sio_client.on("status_update")
def on_status_update(data):
    if "status_updates" not in received_events:
        received_events["status_updates"] = []
    received_events["status_updates"].append(data)


@sio_client.on("long_event")
def on_finished(data):
    received_events["long_event"] = data


def test_async_events():
    sio_client.connect("http://localhost:5000")
    socket_session_id = received_events["connected"]

    sio_client.emit("ping_event", {"socket_session_id": socket_session_id})
    sio_client.emit("listen_to_updates", {"socket_session_id": socket_session_id})
    sio_client.emit("custom_event", {"user": "Pedro", "msg": "Teste", "socket_session_id": socket_session_id})
    sio_client.wait()

    assert "connected" in received_events
    assert received_events.get("pong") == {"message": "pong"}
    assert len(received_events.get("status_updates", [])) == 5
    assert "long_event" in received_events
    assert "disconnect" in received_events