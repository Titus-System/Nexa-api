from typing import Dict, Optional
from pydantic import BaseModel

from app.pdf_parsers.protocols import PartnumberInfo


class AISingleClassificationRequest(BaseModel):
    progress_channel: str
    partnumber: str
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    supplier: Optional[str] = None


class AIBatchClassificationRequest(BaseModel):
    progress_channel: str
    partnumbers: Dict[str, PartnumberInfo]
    