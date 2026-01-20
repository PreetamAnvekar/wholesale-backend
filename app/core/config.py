from pydantic_settings import BaseSettings
import dotenv

dotenv.load_dotenv()



class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "stationery_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "Preetam77"

    class Config:
        env_file = ".env"

settings = Settings()
