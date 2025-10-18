from typing import Optional
from pydantic import BaseModel


class AISingleClassificationRequest(BaseModel):
    progress_channel: str
    partnumber: str
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    supplier: Optional[str] = None


class AIBatchClassificationRequest(BaseModel):
    progress_channel: str
    partnumbers: list[str]
    