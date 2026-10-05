import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações Centrais do HUDSON DC (HDC)
    Ambiente: Oracle Cloud Infrastructure (OCI) / daisugi-net
    """
    APP_NAME: str = "HUDSON Core DC (Event Hub & Webhook Broker)"
    APP_VERSION: str = "1.2.0"
    PORT: int = 9000
    DEBUG: bool = False

    # Redis & Celery (Broker de baixa latência e fila distribuída)
    REDIS_URL: str = "redis://redis:6379/0"

    # Chaves de Segurança e Autenticação Inter-Sistemas
    HUDSON_WEBHOOK_SECRET: str = "daisugi_hudson_secret_sha256_shared_key"
    HUDSON_TOKEN_JWT: str = "token_jwt_operador_secreto"
    DEFAULT_TENANT_ID: str = "sugoi_sa"

    # Integração com a DAI (Smart Reception)
    DAI_CALLBACK_URL: str = "http://dai:8001/api/webhooks/hudson-callback"
    DAI_TIMEOUT_SECONDS: float = 3.0

    # Integrações Adjacentes Daisugi
    KANSA_API_URL: str = "http://kansa:8002"
    KIGYOU_API_URL: str = "http://kigyou:8003"
    PAM_IGA_API_URL: str = "http://pam-iga:8004"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
