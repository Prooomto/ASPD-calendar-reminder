from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://username:password@localhost:5432/calendar_db"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"
    bot_token: str = ""
    api_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()


