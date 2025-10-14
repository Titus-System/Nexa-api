from typing import Any, Dict, Protocol

from app.schemas.classification_schemas import StartSingleClassificationSchema


class IClassificationService(Protocol):
    def start_single_classification(self, schema):
        ...


class IAsyncTaskClient(Protocol):
    def run_single_classification_task(self, schema: StartSingleClassificationSchema) -> str:
        """
        Inicia Tarefa assíncrona e retorna o id da task
        """
        ...

    def run_batch_classification_task(self, schema: Any) -> str:
        """
        Inicia Tarefa assíncrona em lote e retorna o id da task
        """
        ...

