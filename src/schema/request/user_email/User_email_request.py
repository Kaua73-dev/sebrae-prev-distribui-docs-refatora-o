from pydantic import BaseModel, EmailStr


class UserEmailRequest(BaseModel):
    user_email_name: EmailStr
    prefix_name: str