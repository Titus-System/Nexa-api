from enum import Enum


class EventName(str, Enum):
    CLASSIFICATION_FINISHED = "classification_finished"
    CLASSIFICATION_UPDATE_STATUS = "classification_update_status"
    BATCH_CLASSIFICATION_FINISHED = "batch_classification_finished"


class RedisChannelName(str, Enum):
    TASK_RESULTS = "task_results"
    TASK_PROGRESS = "task_progress"
    BATCH_TASK_DONE = "batch_task_done"