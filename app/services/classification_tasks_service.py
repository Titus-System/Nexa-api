from app.models.models import ClassificationTask
from app.extensions import db
from sqlalchemy import update

class ClassificationTaskService:
    def __init__(self):
        self.db_session = db.session


    def read(task_id: str) -> ClassificationTask:
        ...


    def create(self, task_id: str, room_id: str, progress_channel: str, user_id: int):
        self.db_session.add(ClassificationTask(
            id=task_id,
            job_id=None,
            room_id=room_id,
            progress_channel=progress_channel,
            status="STARTED",
            current=0,
            total=3,
            message="Tarefa iniciada",
            user_id=user_id
        ))
        self.db_session.commit()
    
    def update(self, task_id:str, update_attr:dict):
        stmt = update(ClassificationTask).where(ClassificationTask.id == task_id).values(**update_attr)
        self.db_session.execute(stmt)
        self.db_session.commit()

    def update_status(self, task_id: str, status: str, current: int = None, total: int = None, message: str = None):
        task = self.db_session.get(ClassificationTask, task_id)
        if not task:
            return
        task.status = status
        if current is not None:
            task.current = current
        if total is not None:
            task.total = total
        if message is not None:
            task.message = message
        self.db_session.commit()

    def mark_as_failed(self, task_id: str, message: str):
        self.update_status(
            task_id=task_id,
            status="FAILED",
            message=message
        )

    def update_from_room_id(self, room_id:str, update_attr:dict):
        stmt = (update(ClassificationTask).where(ClassificationTask.room_id == room_id).values(**update_attr))
        self.db_session.execute(stmt)
        self.db_session.commit()


classification_task_service = ClassificationTaskService()