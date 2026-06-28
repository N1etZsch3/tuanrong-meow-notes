from fastapi import APIRouter

from app.api.v1.admin_users import router as admin_users_router
from app.api.v1.auth import router as auth_router
from app.api.v1.cats import router as cats_router
from app.api.v1.files import router as files_router
from app.api.v1.health import router as health_router
from app.api.v1.map import router as map_router
from app.api.v1.me import router as me_router
from app.api.v1.profile import router as profile_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(admin_users_router, prefix="/admin/users")
api_router.include_router(cats_router, prefix="/cats")
api_router.include_router(files_router, prefix="/files")
api_router.include_router(map_router, prefix="/map")
api_router.include_router(me_router, prefix="/me")
api_router.include_router(profile_router, prefix="/profile")
