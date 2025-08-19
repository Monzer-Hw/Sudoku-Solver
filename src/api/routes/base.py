from fastapi import APIRouter, Depends
from src.api.config import Settings, get_settings

base_router = APIRouter(
    prefix="/base",
    tags=["base"],
)


@base_router.get("/")
async def read(settings: Settings = Depends(get_settings)):
    settings = get_settings()
    app_name = settings.APP_NAME
    app_version = settings.APP_VERSION
    return {"message": f"{app_name} {app_version}"}
