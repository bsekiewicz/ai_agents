import os
import time
import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import settings

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO if not settings.app.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Upewnij się, że katalogi istnieją
os.makedirs(settings.storage.DATA_DIR, exist_ok=True)

# Inicjalizacja aplikacji
app = FastAPI(
    title=settings.app.PROJECT_NAME,
    description="API do OCR paragonów przy użyciu AI",
    version=settings.app.VERSION,
    openapi_url=f"{settings.app.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W środowisku produkcyjnym lepiej ograniczyć do konkretnych domen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware do logowania czasu odpowiedzi
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Obsługa błędów walidacji
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Błąd walidacji: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Błąd walidacji danych",
            "errors": exc.errors()
        },
    )

# Ogólny handler błędów HTTP
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP Wyjątek: {exc.detail}", exc_info=True)
    return await http_exception_handler(request, exc)

# Obsługa nieoczekiwanych wyjątków
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Nieoczekiwany wyjątek: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Wystąpił nieoczekiwany błąd serwera",
            "type": type(exc).__name__
        },
    )

# Dodaj wszystkie routery
app.include_router(api_router, prefix=settings.app.API_V1_STR)

@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Prosty endpoint do sprawdzenia, czy API działa"""
    return {
        "status": "OK",
        "version": settings.app.VERSION,
        "environment": "development" if settings.app.DEBUG else "production",
        "openai_api_configured": bool(settings.openai.API_KEY),
        "available_prompt_versions": settings.get_all_prompt_versions(),
        "default_prompt_version": settings.storage.DEFAULT_PROMPT_VERSION,
    }

# Logger startowy
@app.on_event("startup")
async def startup_event():
    logger.info(f"Uruchomiono aplikację {settings.app.PROJECT_NAME} v{settings.app.VERSION}")
    logger.info(f"Model LLM: {settings.openai.DEFAULT_MODEL}")
    logger.info(f"Domyślna wersja promptu: {settings.storage.DEFAULT_PROMPT_VERSION}")
    logger.info(f"Dostępne wersje promptów: {settings.get_all_prompt_versions()}")
