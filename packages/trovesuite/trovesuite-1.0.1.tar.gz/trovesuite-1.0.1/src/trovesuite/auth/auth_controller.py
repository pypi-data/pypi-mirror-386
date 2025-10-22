from fastapi import APIRouter
from src.trovesuite.auth.auth_write_dto import AuthControllerWriteDto
from src.trovesuite.auth.auth_read_dto import AuthControllerReadDto
from src.trovesuite.auth.auth_service import AuthService

auth_router = APIRouter()

@auth_router.post("/auth", response_model=AuthControllerReadDto)
async def authorize(data: AuthControllerWriteDto):
    return AuthService.authorize(data=data)