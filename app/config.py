from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = 'Nexa'
    ENVIRONMENT: str = 'development'

    CELERY_BROKER_URL: str = ""

    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT == 'production'

    model_config = ConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8"
    )


settings = Settings()