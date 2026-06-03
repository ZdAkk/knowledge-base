from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "knowledge"
    db_user: str = "postgres"
    db_password: str = ""

    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-large"
    embedding_dims: int = 3072

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
