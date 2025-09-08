from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = 'Nexa'
    ENVIRONMENT: str = 'development'

    CELERY_BROKER_URL: str = ""

    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT == 'production'

    class Config:
        env_file = ".env"
        # Para compatibilidade com Pydantic V1, caso necessário no futuro
        env_file_encoding = 'utf-8'


settings = Settings()