import time
from celery.result import AsyncResult
from app.events.classification_events import finished
from app.extensions import celery
from app.services.protocols import IAsyncTaskClient


class CeleryTaskClient(IAsyncTaskClient):
    def run_task(self, task_data):
        task: AsyncResult = classification_task.delay(**task_data)
        return task.id


@celery.task(bind=True)
def classification_task(self, partnumber):
    for i in range(5):
        time.sleep(2)
        print("classification_progress: ", i)

    result = {
        "partnumber": partnumber,
        "classification": "1234.56.78",
        "status": "done"
    }
    finished(result)