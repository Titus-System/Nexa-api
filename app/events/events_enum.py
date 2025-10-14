from enum import Enum


class EventName(str, Enum):
    CLASSIFICATION_FINISHED = "classification_finished"
    CLASSIFICATION_UPDATE_STATUS = "classification_update_status"


class RedisChannelName(str, Enum):
    TASK_RESULTS = "task_results"
    TASK_PROGRESS = "task_progress"