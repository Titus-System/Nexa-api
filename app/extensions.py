import json
from typing import Dict
from celery import Celery
from flask_socketio import SocketIO
import redis
from app.config import settings
from app.core.logger_config import logger

socketio = SocketIO(
    cors_allowed_origins="*",
    redis_url=settings.REDIS_URL,
)

celery = Celery(
    "myapp",
    backend=settings.REDIS_URL,
    broker=settings.REDIS_URL
)


def init_celery(app):
    logger.info("Inicializando celery...")
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    logger.info("Celery iniciado.")
    return celery
