from datetime import datetime, timedelta
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from src.dependencies import DatabaseSession
from src.models import User


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def is_password_correct(password, existing_password_hash):
    return password_context.verify(password, existing_password_hash)


def retrieve_user_by_credentials(database, username, password):
    user = database.query(User).filter(User.username == username).first()
    if not is_password_correct(password, user.hashed_password):
        return False
    return user


def retrieve_user_by_access_token(database: DatabaseSession, token = Depends(oauth2_scheme)):
    claims = jwt.decode(token, key='1892dhianiandowqd0n', algorithms=["HS256"])
    return database.query(User).filter(User.username == claims.get("sub")).first()


def create_access_token(claims, valid_duration=None):
    """create access token"""
    claims = claims.copy()
    if valid_duration:
        expiration_time = datetime.utcnow() + valid_duration
    else:
        expiration_time = datetime.utcnow() + timedelta(minutes=15)
    claims.update({"exp": expiration_time})
    token = jwt.encode(claims, key='1892dhianiandowqd0n', algorithm="HS256")
    return token