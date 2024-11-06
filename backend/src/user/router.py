from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.dependencies import DatabaseSession
from . import service
from .dependencies import CurrentLoggedInUser
from .schemas import UserRegistrationRequestSchema


router = APIRouter(prefix="/api/v1/users")


@router.post("/login")
async def login_for_access_token(
        database: DatabaseSession,
        form_response: OAuth2PasswordRequestForm = Depends()
):
    access_token = service.login(database, form_response.username, form_response.password)
    return access_token


@router.post("/register")
def register_user(registration: UserRegistrationRequestSchema, database: DatabaseSession):
    new_user = service.register_user(database, registration.username, registration.password)
    return new_user


@router.get("/me")
def read_users_me(user: CurrentLoggedInUser):
    return {"username": user.username}