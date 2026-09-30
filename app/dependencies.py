# app/dependencies.py - Dependency Injection for FastAPI

from app.config import settings, Settings


def get_settings() -> Settings:
    return settings
