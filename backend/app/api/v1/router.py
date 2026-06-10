from fastapi import APIRouter

from .routes.auth import router as auth_router
from .routes.exam import router as exam_router
from .routes.jar import router as jar_router
from .routes.words import router as words_router

router = APIRouter(prefix="/api/v1")
router.include_router(words_router)
router.include_router(jar_router)
router.include_router(exam_router)
router.include_router(auth_router)