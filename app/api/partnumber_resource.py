from flask_restful import Resource

from app.schemas.model_schemas import PartnumberSchema
from app.services.partnumber_service import PartnumberService
from app.core.logger_config import logger


class PartnumberResource(Resource):
    def __init__(self):
        self.service = PartnumberService()
        self.logger = logger
    
    def get(self, partnumber:str=None):
        if partnumber:
            partnumber = partnumber.strip().upper()
            return self.get_one(partnumber)
        return self.get_all()
    
    def get_all(self):
        partnumbers = self.service.get_all_partnumbers()
        partnumbers = [PartnumberSchema.model_validate(p).to_dict() for p in partnumbers]
        return partnumbers

    def get_one(self, partnumber:str):
        pn = self.service.get_one_partnumber(partnumber)
        pn = PartnumberSchema.model_validate(pn).to_dict()
        return pn