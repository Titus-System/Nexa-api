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
        
    def create(self, **kwargs) -> Tipi:
        ncm_code = kwargs.get("ncm_code")
        if not ncm_code:
            raise ValueError("ncm_code é obrigatório")

        existing = (
            self.db_session.query(Tipi)
            .join(Ncm)
            .filter(Tipi.ex == "00", Ncm.code == ncm_code)
            .one_or_none()
        )
        if existing:
            return existing

        ncm = self.db_session.query(Ncm).filter_by(code=ncm_code).one()
        new_tipi = Tipi(ex="00", ncm=ncm)

        self.db_session.add(new_tipi)
        self.db_session.commit()
        self.db_session.refresh(new_tipi)
        return new_tipi