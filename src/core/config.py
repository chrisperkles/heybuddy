"""
Configuration management for heyBuddy
"""
import os
import yaml
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application settings
    app_name: str = "heyBuddy"
    version: str = "0.1.0"
    debug: bool = False
    environment: str = Field(default="development", env="ENVIRONMENT")
    language: str = Field(default="de", env="LANGUAGE")  # "en" or "de"
    
    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8080, env="API_PORT")
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # OpenAI settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=150, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # Audio settings
    audio_device: str = Field(default="auto", env="AUDIO_DEVICE")  # "auto", "mock", "powerconf"
    sample_rate: int = Field(default=16000, env="SAMPLE_RATE")
    chunk_size: int = Field(default=1024, env="CHUNK_SIZE")
    
    # Database settings
    database_url: str = Field(default="sqlite:///./data/heybuddy.db", env="DATABASE_URL")
    
    # Safety settings
    enable_moderation: bool = Field(default=True, env="ENABLE_MODERATION")
    max_conversation_length: int = Field(default=10, env="MAX_CONVERSATION_LENGTH")
    conversation_timeout: int = Field(default=300, env="CONVERSATION_TIMEOUT")  # 5 minutes
    
    # Systemd settings
    enable_systemd_notify: bool = Field(default=False, env="ENABLE_SYSTEMD_NOTIFY")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_file: Optional[str] = None) -> Settings:
    """Load configuration from file and environment variables"""
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Override with environment variables
        for key, value in config_data.items():
            if not os.getenv(key.upper()):
                os.environ[key.upper()] = str(value)
    
    return Settings()


# Global configuration instance
settings = load_config()