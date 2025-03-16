import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Wczytaj zmienne środowiskowe z .env
load_dotenv()


class AppSettings(BaseModel):
    """Konfiguracja aplikacji"""
    PROJECT_NAME: str = "Paragon OCR API"
    API_V1_STR: str = ""
    DEBUG: bool = Field(default=False)
    VERSION: str = "1.0.0"


class OpenAISettings(BaseModel):
    """Konfiguracja OpenAI"""
    API_KEY: str = Field(default="")
    DEFAULT_MODEL: str = Field(default="gpt-4o")
    MAX_TOKENS: int = Field(default=2500)

    @validator("API_KEY")
    def validate_api_key(cls, v):
        if not v and os.getenv("OPENAI_API_KEY"):
            return os.getenv("OPENAI_API_KEY")
        return v


class StorageSettings(BaseModel):
    """Konfiguracja przechowywania danych"""
    DATA_DIR: str = Field(default="data")
    PROMPT_DIR: str = Field(default="app/resources/prompts")
    DEFAULT_PROMPT_VERSION: str = Field(default="1_0_3")
    CACHE_ENABLED: bool = Field(default=True)


class Settings(BaseModel):
    """Główne ustawienia aplikacji"""
    app: AppSettings = Field(default_factory=AppSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)

    def __init__(self, **data: Any):
        """Inicjalizuje ustawienia z pliku konfiguracyjnego lub zmiennych środowiskowych"""
        config_path = os.getenv("CONFIG_FILE", "config.json")

        # Jeśli istnieje plik konfiguracyjny, wczytaj go
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config_data = json.load(f)
                data = {**config_data, **data}
            except Exception as e:
                print(f"Błąd wczytywania pliku konfiguracyjnego: {e}")

        # Wczytaj ustawienia z zmiennych środowiskowych
        env_app_settings = {
            "PROJECT_NAME": os.getenv("PROJECT_NAME"),
            "API_V1_STR": os.getenv("API_V1_STR"),
            "DEBUG": os.getenv("DEBUG", "").lower() in ("true", "1", "t"),
            "VERSION": os.getenv("VERSION")
        }

        env_openai_settings = {
            "API_KEY": os.getenv("OPENAI_API_KEY"),
            "DEFAULT_MODEL": os.getenv("DEFAULT_LLM_MODEL"),
            "MAX_TOKENS": os.getenv("MAX_TOKENS")
        }

        env_storage_settings = {
            "DATA_DIR": os.getenv("DATA_DIR"),
            "PROMPT_DIR": os.getenv("PROMPT_DIR"),
            "DEFAULT_PROMPT_VERSION": os.getenv("DEFAULT_PROMPT_VERSION"),
            "CACHE_ENABLED": os.getenv("CACHE_ENABLED", "").lower() in ("true", "1", "t")
        }

        # Usuń None z słowników, aby nie nadpisywały wartości domyślnych
        app_settings = {k: v for k, v in env_app_settings.items() if v is not None}
        openai_settings = {k: v for k, v in env_openai_settings.items() if v is not None}
        storage_settings = {k: v for k, v in env_storage_settings.items() if v is not None}

        # Utwórz strukturę danych dla BaseModel
        merged_data = {
            "app": {**(data.get("app", {}) or {}), **app_settings},
            "openai": {**(data.get("openai", {}) or {}), **openai_settings},
            "storage": {**(data.get("storage", {}) or {}), **storage_settings}
        }

        super().__init__(**merged_data)

    def get_all_prompt_versions(self) -> List[str]:
        """Pobiera listę wszystkich dostępnych wersji promptów"""
        prompt_dir = Path(self.storage.PROMPT_DIR)
        if not prompt_dir.exists():
            return []

        versions = []
        for file in prompt_dir.glob("ocr_v*.txt"):
            version = file.stem.replace("ocr_v", "")
            versions.append(version)

        return sorted(versions)

    @property
    def OPENAI_API_KEY(self) -> str:
        """Kompatybilność wsteczna"""
        return self.openai.API_KEY

    @property
    def DEFAULT_LLM_MODEL(self) -> str:
        """Kompatybilność wsteczna"""
        return self.openai.DEFAULT_MODEL

    @property
    def DATA_DIR(self) -> str:
        """Kompatybilność wsteczna"""
        return self.storage.DATA_DIR

    @property
    def PROMPT_DIR(self) -> str:
        """Kompatybilność wsteczna"""
        return self.storage.PROMPT_DIR

    @property
    def DEFAULT_PROMPT_VERSION(self) -> str:
        """Kompatybilność wsteczna"""
        return self.storage.DEFAULT_PROMPT_VERSION

    @property
    def PROJECT_NAME(self) -> str:
        """Kompatybilność wsteczna"""
        return self.app.PROJECT_NAME

    @property
    def API_V1_STR(self) -> str:
        """Kompatybilność wsteczna"""
        return self.app.API_V1_STR


# Utwórz instancję ustawień
settings = Settings()
