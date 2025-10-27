from sqlalchemy import select
from app.core.logger_config import logger
from app.extensions import db
from app.models.models import Ncm, Tipi

class TipiService:
    def __init__(self):
        self.logger = logger
        self.db_session = db.session

    def find_from_ncm_ex(self, ncm:str, ex:str|None) -> Tipi | None:
        if ex is None: ex = "00"
        stmt = (
            select(Tipi)
            .join(Tipi.ncm)
            .where(Ncm.code == ncm, Tipi.ex == ex)
        )
        tipi = self.db_session.execute(stmt).scalar_one_or_none()
        return tipi