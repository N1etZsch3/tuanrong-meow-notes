from fastapi import APIRouter

from app.api.v1.admin_landmarks import router as admin_landmarks_router
from app.api.v1.admin_map import router as admin_map_router
from app.api.v1.admin_medicines import router as admin_medicines_router
from app.api.v1.admin_supplies import router as admin_supplies_router
from app.api.v1.admin_tasks import router as admin_tasks_router
from app.api.v1.admin_titles import router as admin_titles_router
from app.api.v1.admin_users import router as admin_users_router
from app.api.v1.auth import router as auth_router
from app.api.v1.cats import router as cats_router
from app.api.v1.files import router as files_router
from app.api.v1.health import router as health_router
from app.api.v1.landmarks import router as landmarks_router
from app.api.v1.map import router as map_router
from app.api.v1.me import router as me_router
from app.api.v1.me_notifications import router as me_notifications_router
from app.api.v1.medicine_applications import router as medicine_applications_router
from app.api.v1.medicine_categories import router as medicine_categories_router
from app.api.v1.medicine_holdings import router as medicine_holdings_router
from app.api.v1.medicines import router as medicines_router
from app.api.v1.profile import router as profile_router
from app.api.v1.public import router as public_router
from app.api.v1.supplies import router as supplies_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.wechat_content_security import router as wechat_content_security_router
from app.api.v1.ws_notifications import router as ws_notifications_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(admin_landmarks_router, prefix="/admin/landmarks")
api_router.include_router(admin_map_router, prefix="/admin/map")
api_router.include_router(admin_medicines_router, prefix="/admin")
api_router.include_router(admin_supplies_router, prefix="/admin/supply-points")
api_router.include_router(admin_tasks_router, prefix="/admin/tasks")
api_router.include_router(admin_titles_router, prefix="/admin/titles")
api_router.include_router(admin_users_router, prefix="/admin/users")
api_router.include_router(cats_router, prefix="/cats")
api_router.include_router(files_router, prefix="/files")
api_router.include_router(landmarks_router, prefix="/landmarks")
api_router.include_router(map_router, prefix="/map")
api_router.include_router(me_router, prefix="/me")
api_router.include_router(me_notifications_router, prefix="/me")
api_router.include_router(medicine_applications_router, prefix="/medicine-applications")
api_router.include_router(medicine_categories_router, prefix="/medicine-categories")
api_router.include_router(medicine_holdings_router, prefix="/medicine-holdings")
api_router.include_router(medicines_router, prefix="/medicines")
api_router.include_router(profile_router, prefix="/profile")
api_router.include_router(public_router, prefix="/public")
api_router.include_router(supplies_router, prefix="/supply-points")
api_router.include_router(tasks_router, prefix="/tasks")
api_router.include_router(wechat_content_security_router, prefix="/wechat/content-security")
api_router.include_router(ws_notifications_router)
