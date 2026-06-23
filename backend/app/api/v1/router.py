from fastapi import APIRouter

from app.api.v1.admin_users import router as admin_users_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(admin_users_router, prefix="/admin/users")
