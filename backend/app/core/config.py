"""
Application configuration settings
"""
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Pokemon Image Recognition API"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/pokemon_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_ttl_pokemon_data: int = 86400  # 24 hours
    redis_ttl_image_results: int = 3600  # 1 hour
    
    # External APIs
    pokeapi_base_url: str = "https://pokeapi.co/api/v2"
    pokeapi_timeout: int = 30
    pokeapi_retry_attempts: int = 3
    
    # AI Model
    ai_model_path: str = "./models/pokemon_classifier.pkl"
    ai_confidence_threshold: float = 0.7
    ai_max_predictions: int = 3
    
    # File Upload
    max_file_size_mb: int = 10
    allowed_file_types: str = "image/jpeg,image/png,image/webp"
    upload_directory: str = "./storage/uploads"
    
    # Security
    secret_key: str = "your-secret-key-here"
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    
    # Performance
    max_concurrent_requests: int = 100
    request_timeout: int = 30
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v: str) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("allowed_file_types", pre=True)
    def assemble_allowed_file_types(cls, v: str) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()