"""
LABBAIK AI v6.0 - Configuration Management
==========================================
Secure configuration handling with environment-based settings,
secrets management, and YAML configuration support.
"""

from __future__ import annotations
import os
import threading
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from functools import lru_cache
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = ""
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    echo: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatabaseConfig":
        return cls(
            url=os.getenv("DATABASE_URL", data.get("url", "")),
            pool_size=data.get("pool_size", 5),
            max_overflow=data.get("max_overflow", 10),
            pool_timeout=data.get("pool_timeout", 30),
            echo=data.get("echo", False)
        )


@dataclass
class AIConfig:
    """AI services configuration."""
    # Groq Configuration
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_tokens: int = 4096
    groq_temperature: float = 0.7

    # OpenAI Configuration (fallback)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # RAG Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5

    # Rate Limiting
    requests_per_minute: int = 30
    tokens_per_minute: int = 100000

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIConfig":
        return cls(
            groq_api_key=os.getenv("GROQ_API_KEY", data.get("groq_api_key", "")),
            groq_model=data.get("groq_model", "llama-3.3-70b-versatile"),
            groq_max_tokens=data.get("groq_max_tokens", 4096),
            groq_temperature=data.get("groq_temperature", 0.7),
            openai_api_key=os.getenv("OPENAI_API_KEY", data.get("openai_api_key", "")),
            openai_model=data.get("openai_model", "gpt-4o-mini"),
            embedding_model=data.get("embedding_model", "all-MiniLM-L6-v2"),
            chunk_size=data.get("chunk_size", 500),
            chunk_overlap=data.get("chunk_overlap", 50),
            top_k_results=data.get("top_k_results", 5),
            requests_per_minute=data.get("requests_per_minute", 30),
            tokens_per_minute=data.get("tokens_per_minute", 100000)
        )


@dataclass
class UmrahDataConfig:
    """Umrah data services configuration (hotels, transport, pricing)."""
    # Amadeus API (Hotel Search)
    amadeus_api_key: str = ""
    amadeus_api_secret: str = ""
    amadeus_environment: str = "test"  # "test" or "production"

    # RapidAPI (Xotelo, etc.)
    rapidapi_key: str = ""

    # Data fetching settings
    cache_duration_hours: int = 24
    max_hotel_results: int = 50
    enable_geocoding: bool = True
    enable_demo_fallback: bool = True

    # Currency
    sar_to_idr_rate: float = 4200.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UmrahDataConfig":
        return cls(
            amadeus_api_key=os.getenv("AMADEUS_API_KEY", data.get("amadeus_api_key", "")),
            amadeus_api_secret=os.getenv("AMADEUS_API_SECRET", data.get("amadeus_api_secret", "")),
            amadeus_environment=data.get("amadeus_environment", "test"),
            rapidapi_key=os.getenv("RAPIDAPI_KEY", data.get("rapidapi_key", "")),
            cache_duration_hours=data.get("cache_duration_hours", 24),
            max_hotel_results=data.get("max_hotel_results", 50),
            enable_geocoding=data.get("enable_geocoding", True),
            enable_demo_fallback=data.get("enable_demo_fallback", True),
            sar_to_idr_rate=data.get("sar_to_idr_rate", 4200.0)
        )


@dataclass
class AuthConfig:
    """Authentication configuration."""
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""
    
    # Session
    session_secret_key: str = ""
    session_expire_hours: int = 24
    
    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthConfig":
        return cls(
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", data.get("google_client_id", "")),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", data.get("google_client_secret", "")),
            google_redirect_uri=data.get("google_redirect_uri", ""),
            session_secret_key=os.getenv("SESSION_SECRET_KEY", data.get("session_secret_key", "")),
            session_expire_hours=data.get("session_expire_hours", 24),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", data.get("jwt_secret_key", "")),
            jwt_algorithm=data.get("jwt_algorithm", "HS256"),
            jwt_expire_minutes=data.get("jwt_expire_minutes", 60)
        )


@dataclass
class UIConfig:
    """UI configuration."""
    app_name: str = "LABBAIK AI"
    app_tagline: str = "Asisten Perjalanan Umrah Cerdas"
    app_version: str = "6.0.0"
    theme: str = "default"
    language: str = "id"
    page_icon: str = "🕋"
    layout: str = "wide"
    
    # Feature Flags
    enable_chat: bool = True
    enable_simulator: bool = True
    enable_booking: bool = True
    enable_umrah_bareng: bool = True
    enable_umrah_mandiri: bool = True
    enable_gamification: bool = True
    enable_pwa: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UIConfig":
        features = data.get("features", {})
        return cls(
            app_name=data.get("app_name", "LABBAIK AI"),
            app_tagline=data.get("app_tagline", "Asisten Perjalanan Umrah Cerdas"),
            app_version=data.get("app_version", "6.0.0"),
            theme=data.get("theme", "default"),
            language=data.get("language", "id"),
            page_icon=data.get("page_icon", "🕋"),
            layout=data.get("layout", "wide"),
            enable_chat=features.get("chat", True),
            enable_simulator=features.get("simulator", True),
            enable_booking=features.get("booking", True),
            enable_umrah_bareng=features.get("umrah_bareng", True),
            enable_umrah_mandiri=features.get("umrah_mandiri", True),
            enable_gamification=features.get("gamification", True),
            enable_pwa=features.get("pwa", True)
        )


@dataclass
class PluginConfig:
    """Plugin system configuration."""
    enabled: bool = True
    plugin_dir: str = "plugins/available"
    auto_load: List[str] = field(default_factory=list)
    disabled: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginConfig":
        return cls(
            enabled=data.get("enabled", True),
            plugin_dir=data.get("plugin_dir", "plugins/available"),
            auto_load=data.get("auto_load", []),
            disabled=data.get("disabled", [])
        )


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoggingConfig":
        return cls(
            level=data.get("level", "INFO"),
            format=data.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=data.get("file_path"),
            max_bytes=data.get("max_bytes", 10485760),
            backup_count=data.get("backup_count", 5)
        )


@dataclass
class Settings:
    """Main application settings container."""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    umrah_data: UmrahDataConfig = field(default_factory=UmrahDataConfig)
    
    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "Settings":
        """Load settings from YAML file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create settings from dictionary."""
        env_str = os.getenv("LABBAIK_ENV", data.get("environment", "development"))
        try:
            environment = Environment(env_str.lower())
        except ValueError:
            logger.warning(f"Invalid LABBAIK_ENV '{env_str}', defaulting to development")
            environment = Environment.DEVELOPMENT

        return cls(
            environment=environment,
            debug=data.get("debug", False),
            database=DatabaseConfig.from_dict(data.get("database", {})),
            ai=AIConfig.from_dict(data.get("ai", {})),
            auth=AuthConfig.from_dict(data.get("auth", {})),
            ui=UIConfig.from_dict(data.get("ui", {})),
            plugins=PluginConfig.from_dict(data.get("plugins", {})),
            logging=LoggingConfig.from_dict(data.get("logging", {})),
            umrah_data=UmrahDataConfig.from_dict(data.get("umrah_data", {}))
        )
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT
    
    def validate(self) -> List[str]:
        """Validate settings and return list of errors."""
        errors = []
        
        # Database validation
        if not self.database.url:
            errors.append("Database URL is required")
        
        # AI validation
        if not self.ai.groq_api_key and not self.ai.openai_api_key:
            errors.append("At least one AI API key (Groq or OpenAI) is required")
        
        # Auth validation (production only)
        if self.is_production():
            if not self.auth.session_secret_key:
                errors.append("Session secret key is required in production")
            if len(self.auth.session_secret_key) < 32:
                errors.append("Session secret key should be at least 32 characters")
        
        return errors


class ConfigManager:
    """
    Configuration manager with thread-safe singleton pattern.
    Provides centralized access to application settings.
    """
    _instance: Optional["ConfigManager"] = None
    _settings: Optional[Settings] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def load(self, config_path: str | Path = "config/settings.yaml") -> Settings:
        """Load configuration from file."""
        self._settings = Settings.from_yaml(config_path)
        
        # Validate settings
        errors = self._settings.validate()
        if errors:
            for error in errors:
                logger.warning(f"Configuration warning: {error}")
        
        return self._settings
    
    def load_from_env(self) -> Settings:
        """Load configuration primarily from environment variables."""
        self._settings = Settings()
        return self._settings
    
    @property
    def settings(self) -> Settings:
        """Get current settings, loading from env if not initialized."""
        if self._settings is None:
            self.load_from_env()
        return self._settings
    
    def reload(self, config_path: str | Path = "config/settings.yaml") -> Settings:
        """Reload configuration from file."""
        return self.load(config_path)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific setting by dot notation (e.g., 'ai.groq_model')."""
        settings = self.settings
        keys = key.split(".")
        value = settings
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default
        
        return value


@lru_cache(maxsize=1)
def get_config() -> ConfigManager:
    """Get the singleton ConfigManager instance."""
    return ConfigManager()


def get_settings() -> Settings:
    """Convenience function to get current settings."""
    return get_config().settings


# Streamlit-specific configuration helpers
def configure_streamlit_page(settings: Optional[Settings] = None):
    """Configure Streamlit page settings."""
    import streamlit as st
    
    settings = settings or get_settings()
    
    st.set_page_config(
        page_title=settings.ui.app_name,
        page_icon=settings.ui.page_icon,
        layout=settings.ui.layout,
        initial_sidebar_state="expanded"
    )


# Environment variable helpers
def get_env(key: str, default: str = "") -> str:
    """Get environment variable with default."""
    return os.getenv(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get environment variable as boolean."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int = 0) -> int:
    """Get environment variable as integer."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_env_list(key: str, default: List[str] = None, separator: str = ",") -> List[str]:
    """Get environment variable as list."""
    value = os.getenv(key)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(separator) if item.strip()]
