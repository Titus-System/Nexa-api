from flask_socketio import SocketIO
from celery.utils.log import get_task_logger
from app.config import settings

celery_logger = get_task_logger(__name__)

external_socketio = SocketIO(message_queue=settings.REDIS_URL)