from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.auth import router as auth_router
from app.api.routes.fiber import router as fiber_router
from app.api.routes.health import router as health_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.operations import router as operations_router
from app.api.routes.rules import router as rules_router
from app.api.routes.subscribers import router as subscribers_router
from app.api.routes.topology import router as topology_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(admin_router, tags=["administration"])
api_router.include_router(inventory_router, prefix="", tags=["inventory"])
api_router.include_router(metrics_router, tags=["metrics"])
api_router.include_router(subscribers_router, tags=["subscribers"])
api_router.include_router(fiber_router, tags=["fiber-access"])
api_router.include_router(topology_router, tags=["topology"])
api_router.include_router(rules_router, tags=["rules"])
api_router.include_router(analysis_router, tags=["analysis"])
api_router.include_router(operations_router, tags=["operations"])
