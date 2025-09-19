import json
import time
from typing import Dict
from celery.result import AsyncResult
from app.events.events_enum import EventName
from app.extensions import celery
from app.schemas.classification_schemas import StartSingleClassificationSchema
from app.services.protocols import IAsyncTaskClient
from . import UpdateStatusDTO, emit_update_status, external_socketio, celery_logger, redis_client


class CeleryTaskClient(IAsyncTaskClient):
    def run_single_classification_task(self, schema:StartSingleClassificationSchema):
        task: AsyncResult = classification_task.delay(schema.model_dump(exclude_none=True))
        return task.id


@celery.task(bind=True)
def classification_task(self, kwargs:Dict):
    room_id = kwargs.get("room_id")
    total_steps = 3
    for i in range(total_steps):
        time.sleep(0.5)
        print(f"classification_progress: {i} for partnumber {kwargs.get('partnumber')}")
        self.update_state(state='PROGRESS',
                          meta={'current': i + 1, 'total': total_steps})
        
        emit_update_status(
            UpdateStatusDTO(**{
                'current': i + 1, 
                'total': total_steps,
                'status': 'processing',
                'message': f'Analisando dados...'
            }),
            room_id
        )

    result = {
        "partnumber": kwargs.get("partnumber"),
        "description": "Descrição detalhada do produto a partir do partnumber",
        "status": "done"
    }

    payload = {
        'room_id': kwargs.get("room_id"),
        'result': result
    }

    redis_client.publish('task_results', json.dumps(payload))

    celery_logger.info(f"Task {self.request.id} completed for partnumber {kwargs.get('partnumber')}")
    return result