from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SCRETE_KEY:str

    model_config={"env_file":".env"}

settings=Settings()