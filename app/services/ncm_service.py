from sqlalchemy import select
from app.core.logger_config import logger
from app.extensions import db
from app.models.models import Ncm

class NcmService:
    def __init__(self):
        self.db_session = db.session
        self.logger = logger

    def get_by_id(self, id: int):
        return
    
    def get_by_code(self, ncm_code:str):
        stmt = select(Ncm).where(Ncm.code == ncm_code)
        result = self.db_session.execute(stmt).scalar_one_or_none()
        return result
    
    def get_all(self):
        stmt = select(Ncm)
        result = self.db_session.execute(stmt).scalars().all()
        return result
    
    def create(self, ncm_code: str) -> Ncm | None:
        existing = self.get_by_code(ncm_code)
        if existing is not None:
            return existing

        register = Ncm(code=ncm_code)
        self.db_session.add(register)
        self.db_session.commit()
        self.db_session.refresh(register)
        return register
    
    