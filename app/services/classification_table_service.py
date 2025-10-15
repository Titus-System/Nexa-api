from sqlalchemy import select
from app.extensions import db
from app.models.models import Classification, Partnumber

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
            manufacturer_id = attributes.get('tipi_id'),
            created_by_user_id = attributes.get('user_id', None),
            short_description = "Short Description",
            long_description = "Long and complete description.",
            confidence_rate = attributes.get("confidence_rate")
        ))
        self.db_session.commit()

    def get_by_task_id(self, task_id:str):
        stmt = select(Classification).where(Classification.classification_task_id == task_id)
        self.db_session.execute(stmt).all()