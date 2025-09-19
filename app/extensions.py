import json
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


def redis_listener():
    print("📢 Ouvinte Redis iniciado, esperando por resultados de tarefas...")
    r = redis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('task_results')

    for message in pubsub.listen():
        print(message)

        try:
            channel = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])

            if channel == 'task_results':
                result = payload.get('result')
                room_id = payload.get('room_id')

                logger.info(f"[INTERCEPTADO]: Resultado para a sala {room_id}. Dados: {result}")

                socketio.emit(
                    'classification_finished',
                    result,
                    to=room_id
                )
                socketio.close_room(room_id)
        except Exception as e:
            logger.error(f"ERRO no ouvinte Redis: {e}")

