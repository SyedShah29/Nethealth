from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(admin_router, tags=["administration"])
api_router.include_router(inventory_router, prefix="", tags=["inventory"])
api_router.include_router(metrics_router, tags=["metrics"])
