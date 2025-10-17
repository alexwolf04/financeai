"""
Configuration settings for FinanceAI
"""
import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./financeai.db"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Security
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # ML Models
    model_cache_ttl: int = 3600  # 1 hour
    max_transactions_for_training: int = 10000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()