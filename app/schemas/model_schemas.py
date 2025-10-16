from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, field_validator

from app.models.models import ClassificationStatus, TaskStatus

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
    id: str
    job_id: str
    room_id: str
    status: TaskStatus
    current: Optional[int] = None
    total: Optional[int] = None
    message: Optional[str] = None
    user_id: int
    classifications: list[ClassificationSchema]


class PartnumberSchema(DTO):
    id: int
    code: str
    best_classification_id: Optional[str] = None
    classifications: Optional[list[ClassificationSchema]] = None
    best_classification: Optional[ClassificationSchema] = None


class TipiSchema(DTO):
    id: int
    ncm_id: int
    ex: str
    description:Optional[str] = None
    tax: float
    classifications: Optional[list[ClassificationSchema]] = None
    ncm: Optional[NcmSchema] = None

    @field_validator("*", mode="before")
    def convert_decimal(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v


class NcmSchema(DTO):
    id: int
    code: str
    description: Optional[str] = None
    tipi_rules: Optional[list[int]]