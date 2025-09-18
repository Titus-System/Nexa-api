from flask_socketio import SocketIO
from celery.utils.log import get_task_logger
import redis
from app.config import settings

celery_logger = get_task_logger(__name__)

external_socketio = SocketIO(message_queue=settings.REDIS_URL)

redis_client = redis.from_url(settings.REDIS_URL)