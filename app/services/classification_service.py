import uuid
from app.api.classification_resource import ClassificationServiceProtocol
from app.extensions import socketio as sio
from app.schemas.classification_schemas import StartClassificationSchema
from app.tasks.classification_task import ClassificationTask


class ClassificationService(ClassificationServiceProtocol):
    @staticmethod
    def start_classification(schema:StartClassificationSchema) -> str:
        
        task_id = str(uuid.uuid4())

        sio.start_background_task(
            ClassificationTask.run,
            schema.partnumber,
            schema.socket_session_id,
            task_id
        )

        return task_id
    

