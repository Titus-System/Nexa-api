from flask import Flask
from flask_cors import CORS
from app.api import initialize_api
from app.config import settings
from app.containers import Container
from app.extensions import init_celery, socketio
from app.core.logger_config import logger

def create_app(container: Container | None = None) -> Flask:
    app = Flask(__name__)
    logger.info("Iniciando aplicação flask")
    CORS(app)
    app.config.update(**settings.model_dump())

    if container is None:
        container = Container()
    app.container = container

    api = initialize_api(app)

    socketio.init_app(app, message_queue=settings.REDIS_URL)
    celery = init_celery(app)
        
    return app
