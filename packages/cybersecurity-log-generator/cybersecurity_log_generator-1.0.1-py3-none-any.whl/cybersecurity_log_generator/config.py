"""
Configuration management for cybersecurity-log-generator.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path


class GeneratorConfig(BaseModel):
    """Configuration for log generators."""
    
    # Default settings
    default_count: int = Field(default=100, description="Default number of logs to generate")
    default_time_range: str = Field(default="24h", description="Default time range for events")
    
    # Output settings
    output_format: str = Field(default="json", description="Default output format")
    include_metadata: bool = Field(default=True, description="Include metadata in generated logs")
    
    # Generator settings
    realistic_patterns: bool = Field(default=True, description="Use realistic attack patterns")
    correlation_enabled: bool = Field(default=True, description="Enable event correlation")
    
    # VictoriaLogs settings
    victorialogs_url: str = Field(default="http://localhost:9428", description="VictoriaLogs URL")
    victorialogs_enabled: bool = Field(default=False, description="Enable VictoriaLogs integration")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=9021, description="API port")
    api_workers: int = Field(default=1, description="Number of API workers")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    class Config:
        env_prefix = "CYBERSECURITY_LOG_"
        case_sensitive = False


def load_config(config_file: Optional[str] = None) -> GeneratorConfig:
    """Load configuration from file and environment variables."""
    
    # Default config
    config_data = {}
    
    # Load from file if provided
    if config_file and Path(config_file).exists():
        import yaml
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
    
    # Load from environment variables
    env_config = {}
    for key, value in os.environ.items():
        if key.startswith("CYBERSECURITY_LOG_"):
            config_key = key.replace("CYBERSECURITY_LOG_", "").lower()
            env_config[config_key] = value
    
    # Merge configurations (env vars override file config)
    merged_config = {**config_data, **env_config}
    
    return GeneratorConfig(**merged_config)


def get_default_config() -> GeneratorConfig:
    """Get default configuration."""
    return GeneratorConfig()


# Global config instance
config = load_config()
