from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # App settings
    debug: bool = False

    # Bot settings
    bot_token: SecretStr = Field(..., description="Telegram bot token")
    
    # App Port
    app_port: int = Field(default=5000)

    # Webhook settings
    webhook_url: str | None = None
    
    # Default user language
    default_language: str = Field(default="ru")

    # PostgreSQL settings
    pg_host: str = Field(default="localhost")
    pg_port: int = Field(default=5432)
    pg_user: str = Field(..., description="PostgreSQL user")
    pg_password: SecretStr = Field(..., description="PostgreSQL password")
    pg_database: str = Field(..., description="PostgreSQL database name")

    # PGAdmin settings
    pgadmin_default_email: str | None = None
    pgadmin_default_password: SecretStr | None = None

    # Redis settings
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_user: str = Field(default="default")
    redis_password: SecretStr | None = None
    redis_database: int = Field(default=0)
    
    redis_cache_ttl: int = Field(default=7)

    logging_enabled: bool = Field(default=False)
    logging_chat_id: int = None
    errors_thread_id: int = Field(default=1)

    # Admin settings
    admin_ids: list[int] = Field(default_factory=list)

    @property
    def tortoise_url(self) -> str:
        """Построить PostgreSQL Tortoise DSN"""
        return (
            f"postgres://{self.pg_user}:"
            f"{self.pg_password.get_secret_value()}@"
            f"{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )

    @property
    def redis_url(self) -> str:
        """Построить Redis DSN"""
        if self.redis_password:
            return (
                f"redis://{self.redis_user}:"
                f"{self.redis_password.get_secret_value()}@"
                f"{self.redis_host}:{self.redis_port}/{self.redis_database}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_database}"


# Синглтон настроек
settings = Settings()