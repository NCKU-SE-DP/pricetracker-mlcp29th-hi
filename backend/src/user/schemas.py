from pydantic import BaseModel


class UserRegistrationRequestSchema(BaseModel):
    username: str
    password: str