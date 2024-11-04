from fastapi import Depends
from src.models import User
from typing import Annotated
from . import service

CurrentLoggedInUser = Annotated[User, Depends(service.retrieve_user_by_access_token)]