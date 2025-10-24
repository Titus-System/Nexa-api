from app.events.events_enum import EventName
from app.extensions import socketio as sio
from app.schemas.classification_schemas import BatchClassificationResponse, SingleClassificationResponse, UpdateStatusResponse
from app.core.logger_config import logger

def single_classification_finished_event(dto: SingleClassificationResponse, room_id: str):
    logger.info(f"[EVENTO] Enviando evento de classificação única para a sala {room_id}")
    sio.emit(
        EventName.CLASSIFICATION_FINISHED.value, 
        dto.model_dump(), 
        to=room_id
    )


def update_status_event(dto: UpdateStatusResponse, room_id):
    logger.info(f"[EVENTO] Enviando evento de atualização {dto.current} / {dto.total} de status para a sala {room_id}")
    sio.emit(
        EventName.CLASSIFICATION_UPDATE_STATUS.value,
        dto,
        to=room_id
    )


def batch_classification_finished_event(dto: BatchClassificationResponse, room_id:str):
    logger.info(f"[EVENTO] Enviando evento final de classificação em lote para a sala {room_id}")
    sio.emit(
        EventName.BATCH_CLASSIFICATION_FINISHED.value,
        dto.model_dump(),
        to=room_id
    )