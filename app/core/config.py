from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8003
    DEBUG: bool = True
    PROJECT_NAME: str = "Notifications Microservice"
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str

    # RabbitMQ - CloudAMQP Support
    RABBITMQ_URL: Optional[str] = None  # URL completa de CloudAMQP (prioridad)
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_QUEUE_NAME: str = "notifications_queue"
    RABBITMQ_EXCHANGE_NAME: str = "notifications"

    # Email Configuration
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    EMAIL_FROM_NAME: str = "Parking System"

    # Firebase Cloud Messaging
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-credentials.json"

    # Retry Configuration
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
