from app.models.models import ClassificationTask, TaskStatus
from app.extensions import db
from sqlalchemy import and_, select, update

class ClassificationTaskService:
    def __init__(self):
        self.db_session = db.session


    def read(self, task_id: str) -> ClassificationTask:
        stmt = select(ClassificationTask).where(ClassificationTask.id == task_id)
        result = self.db_session.execute(stmt).scalar_one_or_none()
        return result

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

    def mark_as_finished(self, task_id: str, data:dict):
        stm = update(ClassificationTask).where(ClassificationTask.id == task_id).values(
            status=TaskStatus.DONE.value,
            current=ClassificationTask.total,
            total=ClassificationTask.total,
            message=data.get("message", "Tarefa concluída com sucesso.")
        )
        self.db_session.execute(stm)
        self.db_session.commit()

    def get_tasks(self, filters: dict):
        stmt = select(ClassificationTask)
        conditions = []
        if "task_id" in filters:
            conditions.append(ClassificationTask.id == filters["task_id"])
        if "user_id" in filters:
            conditions.append(ClassificationTask.user_id == filters["user_id"])
        if "status" in filters:
            conditions.append(ClassificationTask.status == filters["status"])
        if "room_id" in filters:
            conditions.append(ClassificationTask.room_id == filters["room_id"])
        if "progress_channel" in filters:
            conditions.append(ClassificationTask.progress_channel == filters["progress_channel"])
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = self.db_session.execute(stmt).scalars().all()
        return result
