from datetime import timedelta
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.dependencies import DatabaseSession
from src.models import User
from . import service
from .dependencies import CurrentLoggedInUser
from .schemas import UserRegistrationRequestSchema


router = APIRouter(prefix="/api/v1/users")


@router.post("/login")
async def login_for_access_token(
        database: DatabaseSession,
        form_response: OAuth2PasswordRequestForm = Depends()
):
    """login"""
    user = service.retrieve_user_by_credentials(database, form_response.username, form_response.password)
    access_token = service.create_access_token(
        claims={"sub": str(user.username)}, valid_duration=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def register_user(registration: UserRegistrationRequestSchema, database: DatabaseSession):
    """register user"""
    hashed_password = service.hash_password(registration.password)
    new_user = User(username=registration.username, hashed_password=hashed_password)
    database.add(new_user)
    database.commit()
    database.refresh(new_user)
    return new_user


@router.get("/me")
def read_users_me(user: CurrentLoggedInUser):
    return {"username": user.username}