from flask_restful import Resource

from app.schemas.model_schemas import NcmSchema
from app.services.ncm_service import NcmService
from app.core.logger_config import logger


class NcmResource(Resource):
    def __init__(self):
        self.service = NcmService()
        self.logger = logger

    def get(self, ncm_code:str=None):
        if ncm_code:
            ncm_code = ncm_code.strip().upper()
            return self.get_one(ncm_code)
        return self.get_all()
    
    def get_all(self):
        ncms = self.service.get_all()
        ncms = [NcmSchema.model_validate(p).to_dict() for p in ncms]
        return ncms

    def get_one(self, ncm_code:str):
        ncm = self.service.get_by_code(ncm_code)
        if ncm is None:
            self.logger.info(f"NCM not found: {ncm_code}")
            return {"message": "NCM not found"}, 404

        # build a minimal response with description and tipi rules
        tipi_rules = []
        for t in getattr(ncm, "tipi_rules", []) or []:
            tipi_rules.append({
                "id": t.id,
                "ex": t.ex,
                "description": t.description,
                "tax": float(t.tax) if t.tax is not None else None,
            })

        response = {
            "id": ncm.id,
            "code": ncm.code,
            "description": ncm.description,
            "tipi_rules": tipi_rules,
        }

        return response