from app.events.events_enum import EventName
from app.extensions import socketio as sio


def finished(dto, sid):
    sio.emit(
        EventName.CLASSIFICATION_FINISHED.value, 
        dto, 
        to=sid
    )

def update_status(dto, sid):
    sio.emit(
        EventName.CLASSIFICATION_UPDATE_STATUS.value,
        dto,
        to=sid
    )
