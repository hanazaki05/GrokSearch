import tomllib
from pathlib import Path
from typing import Any

class Config:
    _instance = None
    _config_data: dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config.toml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, "rb") as f:
            self._config_data = tomllib.load(f)
    
    @property
    def debug_enabled(self) -> bool:
        return self._config_data.get("debug", {}).get("enabled", False)
    
    @property
    def grok_api_url(self) -> str:
        url = self._config_data.get("grok", {}).get("api_url")
        if not url:
            raise ValueError("grok.api_url not configured")
        return url
    
    @property
    def grok_api_key(self) -> str:
        key = self._config_data.get("grok", {}).get("api_key")
        if not key:
            raise ValueError("grok.api_key not configured")
        return key
    
    @property
    def log_level(self) -> str:
        return self._config_data.get("logging", {}).get("level", "INFO")
    
    @property
    def log_dir(self) -> str:
        return self._config_data.get("logging", {}).get("dir", "logs")

config = Config()
