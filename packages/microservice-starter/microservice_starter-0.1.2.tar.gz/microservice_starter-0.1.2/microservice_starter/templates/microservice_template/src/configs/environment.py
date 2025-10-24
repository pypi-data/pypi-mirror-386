import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


def get_env_filename():
    # Get the runtime environment (e.g., dev, prod, test)
    runtime_env = os.getenv("ENV")
    return f"./env/.env.{runtime_env}" if runtime_env else "./env/.env"


class EnvironmentSettings(BaseSettings):
    API_VERSION: str
    APP_NAME: str
    APP_PORT: int

    # SQL
    DATABASE_DIALECT: str
    DATABASE_HOSTNAME: str
    DATABASE_NAME: str
    DATABASE_PASSWORD: str
    DATABASE_PORT: int
    DATABASE_USERNAME: str
    DEBUG_MODE: bool

    # Redis
    REDIS_CONTAINER_NAME: str
    REDIS_PORT: int

    # Rabbit MQ
    MANAGEMENT_UI: str
    AMQP_PROTOCOL: str
    DEFAULT_USER: str
    DEFAULT_PASS: str
    # RABBIT Redis
    REDIS_RABBIT_CONTAINER_NAME: str
    REDIS_RABBIT_PORT: str

    # Token and secure Variables
    AUTH_SERVICE_URL: str
    LOG_SERVICE_URL: str
    COMPANY_SERVICE_URL: str
    MODEL_SERVICE_URL: str
    CORS_ORIGINS: str

    class Config:
        env_file = get_env_filename()
        env_file_encoding = "utf-8"


def get_environment_variables():
    # Load the correct .env file (this will now happen when you call this function)
    load_dotenv(get_env_filename())

    # Load settings using pydantic BaseSettings
    settings = EnvironmentSettings()
    return settings
