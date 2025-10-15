from datetime import datetime
import decimal
from pydantic import BaseModel
from sqlalchemy import inspect, select
from app.extensions import db
from app.models.models import Classification, Partnumber
from app.core.logger_config import logger
from app.schemas.model_schemas import ClassificationSchema

class PartnumberService:
    def __init__(self):
        self.db_session = db.session
        self.logger = logger

    def create(self, partnumber:str):
        partnumber = partnumber.strip().upper()
        stmt = self.db_session.query(Partnumber).filter(Partnumber.code == partnumber)
        existing_partnumber = stmt.first()
        if existing_partnumber:
            self.logger.info(f"Partnumber já existe: {partnumber}")
            return existing_partnumber
        else:
            self.logger.info(f"Criando novo partnumber: {partnumber}")
            self.db_session.add(Partnumber(code = partnumber))

    def get_classifications(self, partnumber: str) -> list[dict]:
        partnumber = partnumber.strip().upper()
        stmt = select(Partnumber).where(Partnumber.code == partnumber)
        existing_partnumber = self.db_session.execute(stmt).scalar_one_or_none()

        if not existing_partnumber:
            return []

        return [
            ClassificationSchema.model_validate(c).model_dump(mode="json")
            for c in existing_partnumber.classifications
        ]