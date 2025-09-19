from typing import Optional
from pydantic import BaseModel, Field


class SingleClassificationRequest(BaseModel):
    partnumber: str = Field(..., min_length=3, description="O partnumber do produto a ser classificado.")
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    supplier: Optional[str] = None


class StartSingleClassificationSchema(SingleClassificationRequest):
    room_id: str = Field(..., description="O ID da sala do Socket.IO para retorno da notificação.")

