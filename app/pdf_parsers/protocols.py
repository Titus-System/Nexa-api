from typing import Optional, Protocol

from pydantic import BaseModel

class PartnumberPdfInfo(BaseModel):
    partnumber: str
    erp_description: Optional[str] = None
    ncm: Optional[str] = None
    manufacturer: Optional[str] = None
    coo: Optional[str] = None


class PdfParser(Protocol):
    def extract_partnumbers(self) -> dict[str, PartnumberPdfInfo]:
        ...