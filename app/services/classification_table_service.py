from sqlalchemy import select, update, and_
from app.extensions import db
from app.models.models import Classification, Partnumber, ClassificationTask
from app.schemas.classification_schemas import SingleClassification

class ClassificationService:
    def __init__(self):
        self.db_session = db.session


    def create(self, attributes: dict):
        partnumber_id = db.session.execute(
                            select(Partnumber.id).where(Partnumber.code == attributes["partnumber"])
                        ).scalar_one_or_none()

        self.db_session.add(Classification(
            partnumber_id = partnumber_id,
            classification_task_id = attributes["classification_task_id"],
            tipi_id = attributes.get('tipi_id'),
            manufacturer_id = attributes.get('manufacturer_id'),
            created_by_user_id = attributes.get('user_id', None),
            short_description = attributes.get("short_description"),
            long_description = attributes.get("long_description"),
            confidence_rate = attributes.get("confidence_rate"),
            country = attributes.get("country")
        ))
        self.db_session.commit()

    def get_by_task_id(self, task_id:str):
        stmt = select(Classification).where(Classification.classification_task_id == task_id)
        self.db_session.execute(stmt).all()

    def get_by_taskid_and_partnumber(self, task_id: str, partnumber: str) -> Classification:
        stmt = (
            select(Classification)
            .join(Classification.partnumber)
            .where(
                Classification.classification_task_id == task_id,
                Partnumber.code == partnumber
            )
        )
        return self.db_session.execute(stmt).scalar_one()

    def get_classifications(self, filters: dict):
        """Get classifications filtered by various criteria, including user_id."""
        stmt = select(Classification)
        conditions = []
        needs_join = False
        
        if "classification_id" in filters:
            conditions.append(Classification.id == filters["classification_id"])
        if "user_id" in filters:
            conditions.append(Classification.created_by_user_id == filters["user_id"])
        if "job_id" in filters or "progress_channel" in filters or "status" in filters:
            needs_join = True
        
        if needs_join:
            stmt = stmt.join(ClassificationTask, Classification.classification_task_id == ClassificationTask.id)
            if "job_id" in filters:
                conditions.append(ClassificationTask.job_id == filters["job_id"])
            if "progress_channel" in filters:
                conditions.append(ClassificationTask.progress_channel == filters["progress_channel"])
            if "status" in filters:
                conditions.append(ClassificationTask.status == filters["status"])
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        result = self.db_session.execute(stmt).scalars().all()
        return result

    def update(self, id:int, update_attr:dict):
        stmt = update(Classification).where(Classification.id == id).values(**update_attr)
        self.db_session.execute(stmt)
        self.db_session.commit()