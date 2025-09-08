from flask import Flask
from flask_cors import CORS

from app.api import initialize_api
from app.config import settings
from app.extensions import socketio
from app.core.logger_config import logger

def create_app():
    app = Flask(__name__)
    logger.info("Iniciando aplicação flask")
    CORS(app)
    app.config.update(**settings.model_dump())
    api = initialize_api(app)

    socketio.init_app(app)

    return app
