from app import create_app

flask_app = create_app(celery_worker=True)
celery = flask_app.celery