from pydantic import BaseModel, EmailStr, Field

from src.model.user import UserRole

MIN_PASSWORD_LENGTH = 8


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    role: UserRole = UserRole.USER
