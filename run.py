import eventlet
eventlet.monkey_patch()
import json
import redis
from app import create_app
from app.extensions import redis_listener, socketio  
import app.events
from app.config import settings

app = create_app()

socketio.start_background_task(redis_listener)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
