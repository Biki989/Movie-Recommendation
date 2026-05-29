import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Settings(BaseSettings):
    PROJECT_NAME: str = "CinematIX Backend API"
    BASE_DIR: str = BASE_DIR
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours for seamless UX
    
    # Database URL: fallback to sqlite inside local backend folder if not provided
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:////tmp/database_production.db" if os.getenv("VERCEL") else f"sqlite:///{os.path.join(BASE_DIR, 'database_production.db')}"
    )
    
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    
    class Config:
        case_sensitive = True

# Validate security essentials
settings = Settings()

if not settings.SECRET_KEY or settings.SECRET_KEY == "cinematix-super-secret-key-2024":
    # In secure production, we should fail early. We will print a major warning for local development.
    print("[WARNING] SECRET_KEY is not set or using insecure default! Please set SECRET_KEY in .env.")
