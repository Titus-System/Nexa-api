import socketio
import time

sio = socketio.Client()

my_sid = None

@sio.event
def connect():
    print("✅ Conectado ao servidor")


@sio.event
def disconnect():
    print("❌ Desconectado do servidor")


@sio.on('connected')
def on_connected(data):
    global my_sid
    my_sid = data.get('sid')
    print(f"[CONNECTED] {data}")


@sio.on('pong_event')
def on_pong(data):
    print(f"[PONG] pong recebido do servidor: {data}")


@sio.on("status_update")
def on_status_update(data):
    print(f"[STATUS_UPDATE] recebida atualização de status: {data}")


@sio.on("message")
def on_message(data):
    print("[MESSAGE]: ", data)


@sio.on("long_event")
def on_response_event(data):
    print("[LONG EVENT]:", data)

@sio.on("finished_mock_task")
def on_finished_mock_task(data):
    print(f"[MOCK TASK]: ", data)


def main():
    global my_sid
    sio.connect("http://localhost:5000")

    sio.emit("custom_event", {"user": "Pedro", "msg": "Testando evento", 'sid': my_sid})
    
    sio.emit("listen_to_updates", {'sid': my_sid})

    sio.send("Olá servidor do Flask!")

    sio.emit('ping_event', {'sid': my_sid})

    sio.wait()


if __name__ == "__main__":
    main()
