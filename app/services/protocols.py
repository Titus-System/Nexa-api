from typing import Any, Dict, Protocol


class IClassificationService(Protocol):
    def start_classification(self, schema):
        ...


class IAsyncTaskClient(Protocol):
    def run_task(self, task_data: Dict[str, Any]) -> str:
        """
        Inicia Tarefa assíncrona e retorna o id da task
        """
        ...


