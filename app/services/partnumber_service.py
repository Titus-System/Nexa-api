from sqlalchemy import select, update
from app.extensions import db
from app.models.models import Classification, Partnumber
from app.core.logger_config import logger

class PartnumberService:
    def __init__(self):
        self.db_session = db.session
        self.logger = logger

    def create(self, partnumber: str) -> Partnumber:
        partnumber = partnumber.strip().upper()
        existing = (
            self.db_session.query(Partnumber)
            .filter(Partnumber.code == partnumber)
            .first()
        )
        if existing:
            self.logger.info(f"Partnumber já existe: {partnumber}")
            return existing

        self.logger.info(f"Criando novo partnumber: {partnumber}")
        new_part = Partnumber(code=partnumber)
        self.db_session.add(new_part)
        self.db_session.commit()
        self.db_session.refresh(new_part)
        return new_part

    def get_classifications(self, partnumber: str) -> list[dict]:
        partnumber = partnumber.strip().upper()
        stmt = select(Partnumber).where(Partnumber.code == partnumber)
        existing_partnumber = self.db_session.execute(stmt).scalar_one_or_none()

        if not existing_partnumber:
            return []

        return [c for c in existing_partnumber.classifications]

    def update_by_id(self, id:int, update_attr:dict):
        stmt = update(Partnumber).where(Partnumber.id == id).values(**update_attr)
        self.db_session.execute(stmt)
        self.db_session.commit()

    def update(self, partnumber:int, update_attr:dict):
        stmt = update(Partnumber).where(Partnumber.code == partnumber).values(**update_attr)
        self.db_session.execute(stmt)
        self.db_session.commit()
    
    def mark_best_classification(self, partnumber:str, classification_id:str):
        self.update(partnumber, {"best_classification_id": classification_id})

    def get_all_partnumbers(self):
        stmt = select(Partnumber)
        result = self.db_session.execute(stmt).scalars().all()
        return result

    def get_one_partnumber(self, partnumber:str):
        stmt = select(Partnumber).where(Partnumber.code == partnumber)
        result = self.db_session.execute(stmt).scalar_one_or_none()
        return result