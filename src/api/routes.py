from fastapi import APIRouter

from src.api.routers.auth_router import router as auth_router
from src.api.routers.dass_router import router as dass_router
from src.api.routers.patient_router import router as patient_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(dass_router)
router.include_router(patient_router)