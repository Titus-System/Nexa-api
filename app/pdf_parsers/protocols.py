from typing import Optional, Protocol

from pydantic import BaseModel, computed_field

class PartnumberInfo(BaseModel):
    partnumber: str
    erp_description: Optional[str] = None
    ncm: Optional[str] = None
    manufacturer: Optional[str] = None
    coo: Optional[str] = None
    address: Optional[str] = None

    coo_map: dict[str,str] = {
        "CN": "CHINA, REPÚBLICA POPULAR",
        "TW": "TAIWAN",
        "MX": "MÉXICO",
        "VN": "VIETNÃ",
        "TH": "TAILÂNDIA",
        "EUA": "ESTADOS UNIDOS",
        "CHINA": "CHINA, REPÚBLICA POPULAR"
    }

    @computed_field
    @property
    def country(self) -> Optional[str]:
        if self.coo is None:
            return None
        c = self.coo_map.get(self.coo)
        if c is None:
            return self.coo
        return c


class PdfParser(Protocol):
    def extract_partnumbers(self) -> dict[str, PartnumberInfo]:
        ...