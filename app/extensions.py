from celery import Celery
from flask_socketio import SocketIO
from app.config import settings
from app.core.logger_config import logger

socketio = SocketIO(cors_allowed_origins="*")

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