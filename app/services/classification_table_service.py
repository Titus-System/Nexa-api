from sqlalchemy import select, update
from app.extensions import db
from app.models.models import Classification, Partnumber
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
            country_code = attributes.get("country_code")
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

    def update(self, id:int, update_attr:dict):
        stmt = update(Classification).where(Classification.id == id).values(**update_attr)
        self.db_session.execute(stmt)
        self.db_session.commit()