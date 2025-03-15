from fastapi import APIRouter
from app.api.endpoints import receipt

api_router = APIRouter()

# Dodaj wszystkie endpointy
api_router.include_router(receipt.router, tags=["receipts"])

# W przyszłości możesz dodać kolejne routery dla innych zasobów API
# np. api_router.include_router(users.router, prefix="/users", tags=["users"])
