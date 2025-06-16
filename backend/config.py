"""
Configuration management for Meeting Dashboard backend
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "Meeting Dashboard API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Security settings
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_hours: int = Field(default=24, env="JWT_EXPIRE_HOURS")
    
    # Zoom OAuth settings
    zoom_client_id: str = Field(..., env="ZOOM_CLIENT_ID")
    zoom_client_secret: str = Field(..., env="ZOOM_CLIENT_SECRET")
    zoom_redirect_uri: str = Field(..., env="ZOOM_REDIRECT_URI")
    zoom_base_url: str = Field(default="https://api.zoom.us/v2", env="ZOOM_BASE_URL")
    zoom_oauth_url: str = Field(default="https://zoom.us/oauth", env="ZOOM_OAUTH_URL")
    
    # File monitoring settings
    zoom_recordings_path: Optional[str] = Field(default=None, env="ZOOM_RECORDINGS_PATH")
    monitor_interval: int = Field(default=30, env="MONITOR_INTERVAL_SECONDS")  # seconds
    supported_file_extensions: list = Field(
        default=[".mp4", ".m4a", ".mp3", ".wav", ".webm"],
        env="SUPPORTED_FILE_EXTENSIONS"
    )
    
    # Supabase settings
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(..., env="SUPABASE_SERVICE_KEY")
    
    # Storage settings (Supabase Storage or S3)
    storage_provider: str = Field(default="supabase", env="STORAGE_PROVIDER")  # "supabase" or "s3"
    storage_bucket: str = Field(default="recordings", env="STORAGE_BUCKET")
    
    # S3 settings (optional, if using S3 instead of Supabase)
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: Optional[str] = Field(default="us-east-1", env="AWS_REGION")
    s3_bucket: Optional[str] = Field(default=None, env="S3_BUCKET")
    
    # Database settings (Supabase PostgreSQL)
    database_url: str = Field(..., env="DATABASE_URL")
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_pool_overflow: int = Field(default=0, env="DB_POOL_OVERFLOW")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Error handling settings
    max_retry_attempts: int = Field(default=3, env="MAX_RETRY_ATTEMPTS")
    retry_delay_seconds: int = Field(default=5, env="RETRY_DELAY_SECONDS")
    
    # File processing settings
    max_file_size_mb: int = Field(default=500, env="MAX_FILE_SIZE_MB")  # 500MB max
    chunk_size_bytes: int = Field(default=8192, env="CHUNK_SIZE_BYTES")  # 8KB chunks
    
    # Notification settings
    enable_notifications: bool = Field(default=True, env="ENABLE_NOTIFICATIONS")
    notification_email: Optional[str] = Field(default=None, env="NOTIFICATION_EMAIL")
    
    # CORS settings
    cors_origins: list = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("zoom_recordings_path")
    def validate_zoom_path(cls, v):
        """Validate and expand Zoom recordings path"""
        if v:
            expanded_path = Path(v).expanduser().resolve()
            if not expanded_path.exists():
                # Create directory if it doesn't exist
                try:
                    expanded_path.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    raise ValueError(f"Cannot create directory: {expanded_path}")
            return str(expanded_path)
        return v
    
    @validator("supported_file_extensions")
    def validate_file_extensions(cls, v):
        """Ensure file extensions start with dot"""
        if isinstance(v, str):
            # Handle comma-separated string from env var
            v = [ext.strip() for ext in v.split(",")]
        
        extensions = []
        for ext in v:
            if not ext.startswith("."):
                ext = f".{ext}"
            extensions.append(ext.lower())
        return extensions
    
    @validator("cors_origins")
    def validate_cors_origins(cls, v):
        """Handle CORS origins from environment variable"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB to bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def zoom_recordings_path_obj(self) -> Optional[Path]:
        """Get Zoom recordings path as Path object"""
        if self.zoom_recordings_path:
            return Path(self.zoom_recordings_path)
        return None
    
    def get_zoom_oauth_authorize_url(self, state: str) -> str:
        """Generate Zoom OAuth authorization URL"""
        return (
            f"{self.zoom_oauth_url}/authorize"
            f"?response_type=code"
            f"&client_id={self.zoom_client_id}"
            f"&redirect_uri={self.zoom_redirect_uri}"
            f"&state={state}"
        )
    
    def get_zoom_oauth_token_url(self) -> str:
        """Get Zoom OAuth token URL"""
        return f"{self.zoom_oauth_url}/token"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance (for dependency injection)"""
    return settings


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    reload: bool = True
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    reload: bool = False
    log_level: str = "INFO"


class TestingSettings(Settings):
    """Testing environment settings"""
    debug: bool = True
    database_url: str = "sqlite:///./test_db.sqlite"
    zoom_recordings_path: str = "/tmp/test_zoom_recordings"


def get_settings_for_environment(env: str = None) -> Settings:
    """Get settings based on environment"""
    if env is None:
        env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings() 