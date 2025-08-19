from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    FILE_ALLOWED_TYPES: list

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings():
    return Settings()
