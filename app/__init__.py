from flask import Flask
from flask_cors import CORS
from app.api import initialize_api
from app.config import settings
from app.containers import Container
from app.database.seed_db import seed_db
from app.core.logger_config import logger
from app.models import *


def create_app(container: Container | None = None) -> Flask:
    app = Flask(__name__)
    logger.info("Iniciando aplicação flask")
    
    CORS(app)
    app.config.update(**settings.model_dump())

    app.config["SQLALCHEMY_DATABASE_URI"] = settings.NEXA_DB_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if container is None:
        container = Container()
    app.container = container

    api = initialize_api(app)

    from app.extensions import init_celery, socketio, db
    socketio.init_app(app, message_queue=settings.REDIS_URL)
    celery = init_celery(app)
    app.celery = celery
        
    db.init_app(app)
    with app.app_context():
        # db.drop_all()
        # db.create_all()
        # seed_db()
        ...

    return app
