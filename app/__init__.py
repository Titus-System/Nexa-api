from flask import Flask
from flask_cors import CORS

from app.api import initialize_api
from app.config import settings


app = Flask(__name__)
CORS(app)

app.config.update(**settings.model_dump())

api = initialize_api(app)
