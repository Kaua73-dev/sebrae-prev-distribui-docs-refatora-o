from pydantic import BaseModel, EmailStr


class UserEmailUpdateRequest(BaseModel):
    id: int
    user_email_name: EmailStr
    prefix_name: str | None = None
    is_active: bool
