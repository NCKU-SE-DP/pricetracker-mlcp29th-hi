from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.models import User
from .config import configuration


_password_context = CryptContext(schemes=[configuration.password_hashing_algorithm], deprecated=["auto"])


def _hash_password(plaintext: str) -> str:
    return _password_context.hash(plaintext)


def _is_password_correct(password, existing_password_hash) -> bool:
    return _password_context.verify(password, existing_password_hash)


def _retrieve_user_by_credentials(database, username, password) -> User | None:
    user = database.query(User).filter(User.username == username).first()
    if not _is_password_correct(password, user.hashed_password):
        return None
    return user


def _create_access_token(claims, valid_duration=None) -> str:
    claims = claims.copy()
    if valid_duration:
        expiration_time = datetime.now() + valid_duration
    else:
        expiration_time = datetime.now() + timedelta(minutes=configuration.access_token_valid_duration)
    claims.update({"exp": expiration_time})
    token = jwt.encode(claims, key=configuration.access_token_secret_key, algorithm=configuration.access_token_algorithm)
    return token


def login(database: Session, username: str, password: str) -> dict:
    user = _retrieve_user_by_credentials(database, username, password)
    access_token = _create_access_token(
        claims={"sub": str(user.username)}, valid_duration=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}


def register_user(database: Session, username: str, password: str) -> User:
    hashed_password = _hash_password(password)
    new_user = User(username=username, hashed_password=hashed_password)
    database.add(new_user)
    database.commit()
    database.refresh(new_user)
    return new_user