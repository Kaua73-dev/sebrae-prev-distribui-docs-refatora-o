from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DispatchBlockResponse(BaseModel):
    id: int
    prefix_name: str
    intended_recipient: str | None
    file_paths: list[str]
    included: bool
    status: str
    delivered_to: str | None
    delivered_at: datetime | None
    attempts: int
    error: str | None

    model_config = ConfigDict(from_attributes=True)


class DispatchResponse(BaseModel):
    id: int
    status: str
    create_at: datetime
    execute_at: datetime | None
    finish_at: datetime | None
    blocks: list[DispatchBlockResponse]
    warnings: list[str] = []
    mail_sending_disabled: bool = False
    mail_redirected_to: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DispatchStatusResponse(BaseModel):
    id: int
    status: str
    total: int
    sent: int
    failed: int
    pending: int
    excluded: int

    model_config = ConfigDict(from_attributes=True)
