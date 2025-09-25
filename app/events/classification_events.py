from app.events.events_enum import EventName
from app.extensions import socketio as sio
from app.schemas.classification_schemas import SingleClassificationResponse, UpdateStatusResponse


def single_classification_finished_event(dto: SingleClassificationResponse, room_id: str):
    sio.emit(
        EventName.CLASSIFICATION_FINISHED.value, 
        dto.model_dump(), 
        to=room_id
    )


def update_status_event(dto: UpdateStatusResponse, room_id):
    sio.emit(
        EventName.CLASSIFICATION_UPDATE_STATUS.value,
        dto,
        to=room_id
    )
