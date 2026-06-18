from pydantic import BaseModel
import os


class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL")


settings = Settings()