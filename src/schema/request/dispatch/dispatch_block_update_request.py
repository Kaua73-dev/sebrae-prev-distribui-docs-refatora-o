from pydantic import BaseModel, EmailStr


class DispatchBlockUpdateRequest(BaseModel):
    included: bool | None = None
    email: EmailStr | None = None
