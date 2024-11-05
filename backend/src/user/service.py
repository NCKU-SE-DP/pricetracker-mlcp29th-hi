from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from src.models import User
from .config import configuration


_password_context = CryptContext(schemes=[configuration.password_hashing_algorithm], deprecated=["auto"])


def hash_password(plaintext: str) -> str:
    return _password_context.hash(plaintext)


def is_password_correct(password, existing_password_hash):
    return _password_context.verify(password, existing_password_hash)


def retrieve_user_by_credentials(database, username, password):
    user = database.query(User).filter(User.username == username).first()
    if not is_password_correct(password, user.hashed_password):
        return False
    return user


def create_access_token(claims, valid_duration=None):
    """create access token"""
    claims = claims.copy()
    if valid_duration:
        expiration_time = datetime.utcnow() + valid_duration
    else:
        expiration_time = datetime.utcnow() + timedelta(minutes=configuration.access_token_valid_duration)
    claims.update({"exp": expiration_time})
    token = jwt.encode(claims, key=configuration.access_token_secret_key, algorithm=configuration.access_token_algorithm)
    return token