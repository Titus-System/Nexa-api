from dependency_injector import containers, providers

from app.services.classification_service import PartnumberClassificationService
from app.tasks.ai_classification_client import AIClassificationClient


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["app.api"]
    )

    celery_client = providers.Singleton(AIClassificationClient)

    classification_service = providers.Singleton(
        PartnumberClassificationService
    )
