from dependency_injector import containers, providers

from app.services.classification_service import ClassificationService
from app.tasks.ai_classification_task import CeleryTaskClientAI
from app.tasks.classification_task import CeleryTaskClient


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["app.api"]
    )

    celery_client = providers.Singleton(CeleryTaskClientAI)

    classification_service = providers.Singleton(
        ClassificationService,
        task_client=celery_client,
    )
