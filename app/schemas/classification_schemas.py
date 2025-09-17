from typing import Optional
from pydantic import BaseModel, Field


class ClassificationRequest(BaseModel):
    partnumber: str = Field(..., min_length=3, description="O partnumber do produto a ser classificado.")
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    # socket_session_id: Optional[str] = Field(..., description="O ID da sessão do cliente no Socket.IO para retorno da notificação.")


class StartClassificationSchema(ClassificationRequest):
    partnumber: str = Field(..., min_length=3, description="O partnumber do produto a ser classificado.")
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    room_id: str = Field(..., description="O ID da sala do Socket.IO para retorno da notificação.")

