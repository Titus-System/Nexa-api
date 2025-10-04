from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = 'Nexa'
    ENVIRONMENT: str = 'development'

    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT == 'production'

    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0 

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "nexa_db"

    NEXA_DB_NAME: str = "nexa_db"
    NEXA_DB_PORT: str = "5432"
    NEXA_DB_USER: str = "postgres"
    NEXA_DB_PASS: str = "postgres"
    NEXA_DB_HOST: str = "db"

    @property
    def NEXA_DB_URL(self) -> str:
        return f"postgresql://{self.NEXA_DB_USER}:{self.NEXA_DB_PASS}@{self.NEXA_DB_HOST}:{self.NEXA_DB_PORT}/{self.NEXA_DB_NAME}"


    model_config = ConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8"
    )

    NEXA_AI_SERVER: str = "http://127.0.0.1:5001"


settings = Settings()