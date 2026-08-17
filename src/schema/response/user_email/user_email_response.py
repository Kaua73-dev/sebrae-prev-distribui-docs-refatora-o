from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class UserEmailResponse(BaseModel):
    id: int
    user_email_name: EmailStr
    is_active: bool
    created_at: datetime
    prefix_name: str


    model_config = ConfigDict(from_attributes=True)
