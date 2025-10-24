from pydantic import Field
from pydantic_settings import BaseSettings


class OpenApiSettings(BaseSettings):
    title: str = Field(deafult="title")
    version: str = Field(deafult="0.1.2")
    path: str = Field(deafult="/api/docs")

    class Config:
        env_prefix = "OPEN_API_"


class Settings(BaseSettings):
    db_url: str = Field(default="postgresql+asyncpg://user:password@localhost:5432/db")
    open_api_config: OpenApiSettings = Field(default_factory=OpenApiSettings)


settings = Settings()
