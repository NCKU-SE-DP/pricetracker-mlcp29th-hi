from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

from src.dependencies import DatabaseSession
from src.models import User
from .config import configuration


_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=configuration.access_token_url)


def _retrieve_user_by_access_token(
        database: DatabaseSession,
        token = Depends(_oauth2_scheme)
):
    claims = jwt.decode(token, key=configuration.access_token_secret_key, algorithms=[configuration.access_token_algorithm])
    return database.query(User).filter(User.username == claims.get("sub")).first()


CurrentLoggedInUser = Annotated[User, Depends(_retrieve_user_by_access_token)]