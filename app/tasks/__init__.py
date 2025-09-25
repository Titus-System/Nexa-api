from flask_socketio import SocketIO
from celery.utils.log import get_task_logger
from pydantic import BaseModel
import redis
from app.config import settings
from app.events.events_enum import EventName

celery_logger = get_task_logger(__name__)

external_socketio = SocketIO(message_queue=settings.REDIS_URL)

redis_client = redis.from_url(settings.REDIS_URL)


class ClassificationFinishedDTO(BaseModel):
    partnumber: str
    description: str
    status: str  # e.g., "done", "failed"
    message: str | None = None  # Optional message field


class UpdateStatusDTO(BaseModel):
    current: int
    total: int
    status: str  # e.g., "processing", "failed"
    message: str | None = None  # Optional message field


def emit_classification_finished(dto, room_id):
    external_socketio.emit(
        EventName.CLASSIFICATION_FINISHED.value, 
        dto, 
        to=room_id
    )


def emit_update_status(dto: UpdateStatusDTO, room_id):
    external_socketio.emit(
        EventName.CLASSIFICATION_UPDATE_STATUS.value,
        dto.model_dump(),
        to=room_id
    )
