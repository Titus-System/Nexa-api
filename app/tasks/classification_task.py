import json
import time
from celery.result import AsyncResult
from app.events.events_enum import EventName
from app.extensions import celery
from app.services.protocols import IAsyncTaskClient
from . import external_socketio, celery_logger, redis_client


class CeleryTaskClient(IAsyncTaskClient):
    def run_task(self, task_data):
        task: AsyncResult = classification_task.delay(task_data)
        return task.id


@celery.task(bind=True)
def classification_task(self, kwargs):
    total_steps = 3
    for i in range(total_steps):
        time.sleep(0.5)
        print(f"classification_progress: {i} for partnumber {kwargs.get('partnumber')}")
        self.update_state(state='PROGRESS',
                          meta={'current': i + 1, 'total': total_steps})
        
        external_socketio.emit(
            EventName.CLASSIFICATION_UPDATE_STATUS.value,
            {'current': i + 1, 'total': total_steps}, 
            to=kwargs.get("room_id")
        )

    result = {
        "partnumber": kwargs.get("partnumber"),
        "classification": "1234.56.78",
        "status": "done"
    }

    payload = {
        'room_id': kwargs.get("room_id"),
        'result': result
    }

    redis_client.publish('task_results', json.dumps(payload))

    celery_logger.info(f"Task {self.request.id} completed for partnumber {kwargs.get('partnumber')}")
    return result