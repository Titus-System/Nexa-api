import eventlet

from app.events.redis_listener import RedisListener
eventlet.monkey_patch()
from app import create_app
from app.extensions import socketio  
from app.events import *

app = create_app()

redis_listener = RedisListener()
socketio.start_background_task(redis_listener.start)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
