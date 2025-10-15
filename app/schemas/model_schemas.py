from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.models import ClassificationStatus

class DTO(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return self.model_dump(mode="json")
    
    model_config = {
        "from_attributes": True
    }


class ClassificationSchema(DTO):
    id: int
    partnumber_id: int
    classification_task_id: str
    tipi_id: Optional[int] = None
    manufacturer_id: Optional[int] = None
    created_by_user_id: int
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    status: Optional[ClassificationStatus] = None
    confidence_rate: Optional[float]


class ClassificationTaskSchema(DTO):
    ...