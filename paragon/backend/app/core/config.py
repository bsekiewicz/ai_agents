import os
from dotenv import load_dotenv

# Wczytaj zmienne środowiskowe z .env
load_dotenv()


class Settings:
    # Konfiguracja aplikacji
    PROJECT_NAME: str = "Paragon OCR API"
    API_V1_STR: str = ""

    # Konfiguracja OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o")

    # Konfiguracja przechowywania danych
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    PROMPT_DIR: str = os.getenv("PROMPT_DIR", "app/resources/prompts")

    # Domyślna wersja promptu
    DEFAULT_PROMPT_VERSION: str = os.getenv("DEFAULT_PROMPT_VERSION", "1_0_3")


# Utwórz instancję ustawień
settings = Settings()
