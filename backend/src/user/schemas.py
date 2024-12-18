from pydantic import BaseModel, Field


class UserRegistrationRequestSchema(BaseModel):
    username: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1)