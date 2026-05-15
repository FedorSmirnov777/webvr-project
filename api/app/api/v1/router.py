from fastapi import APIRouter

from app.api.v1 import auth, brands, cars, commerce

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(brands.router, prefix="/brands", tags=["brands"])
api_router.include_router(cars.router, prefix="/cars", tags=["cars"])
api_router.include_router(commerce.router, prefix="/commerce", tags=["commerce"])
