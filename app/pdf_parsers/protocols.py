from typing import Optional, Protocol

from pydantic import BaseModel

class PartnumberInfo(BaseModel):
    partnumber: str
    erp_description: Optional[str] = None
    ncm: Optional[str] = None
    manufacturer: Optional[str] = None
    coo: Optional[str] = None
    address: Optional[str] = None


class PdfParser(Protocol):
    def extract_partnumbers(self) -> dict[str, PartnumberInfo]:
        ...