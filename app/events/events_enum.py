from enum import Enum


class EventName(str, Enum):
    CLASSIFICATION_FINISHED = "classification_finished"
    CLASSIFICATION_UPDATE_STATUS = "classification_update_status"
    