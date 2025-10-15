from typing import Dict, Optional, Type, TypeVar
from pydantic import BaseModel, Field, ValidationError
from app.core.logger_config import logger
from app.models.models import TaskStatus


T = TypeVar('T', bound=BaseModel)


class SingleClassificationRequest(BaseModel):
    partnumber: str = Field(..., min_length=3, description="O partnumber do produto a ser classificado.")
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    supplier: Optional[str] = None
    user_id: Optional[int] = 1
    reclassify: Optional[bool] = False


class StartSingleClassificationSchema(SingleClassificationRequest):
    room_id: str = Field(..., description="O ID da sala do Socket.IO para retorno da notificação.")


class SingleClassification(BaseModel):
    partnumber : Optional[str] = None
    ncm : Optional[str] = None
    description : Optional[str] = None
    exception : Optional[str] = None
    nve : Optional[str] = None
    fabricante : Optional[str] = None
    endereco : Optional[str] = None
    pais : Optional[str] = None
    confidence_score: Optional[float]


class SingleClassificationResponse(BaseModel):
    status: str
    message: str
    partnumber: str
    result: SingleClassification


class UpdateStatusResponse(BaseModel):
    status: TaskStatus
    current: Optional[int]
    total: Optional[int]
    message: Optional[str]

class FailedStatusResponse(BaseModel):
    status: TaskStatus
    job_id: Optional[str] = None
    message: Optional[str] = None


def validate_and_get_model(data_to_validate: Dict[str, any], model:Type[T]) -> Optional[T]:
    """
    Valida um dicionário contra um modelo Pydantic.
    Retorna o dicionário validado em caso de sucesso, ou None em caso de erro.
    """
    try:
        validated_object = model.model_validate(data_to_validate)
        return validated_object
    except ValidationError as e:
        logger.info(f"Falha na validação do modelo {model.__name__}: {e}")
        return None