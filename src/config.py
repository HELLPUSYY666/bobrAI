from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "taskdb"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_queue: str = "tasks"
    
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    @property
    def sync_db_url(self) -> str:
        return self.database_url.replace('asyncpg', 'psycopg2')
    
    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/"
        )


settings = Settings()
