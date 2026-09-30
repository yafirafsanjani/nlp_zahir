# app/config.py - Configuration & Environment Variables for FastAPI

import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = 'NLP Support Center Zahir API'
    VERSION: str = '1.0.0'
    DESCRIPTION: str = 'FastAPI Core Backend untuk Ingestion dan NLP Analytics Engine Zahir Support'
    API_HOST: str = os.getenv('API_HOST', '127.0.0.1')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')
        if origin.strip()
    ]
    UPLOAD_MAX_SIZE_MB: int = int(os.getenv('UPLOAD_MAX_SIZE_MB', '100'))


settings = Settings()
