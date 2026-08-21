from pydantic import BaseModel

BEARER = "bearer"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = BEARER
