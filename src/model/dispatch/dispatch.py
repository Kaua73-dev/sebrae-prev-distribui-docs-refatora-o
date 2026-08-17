from datetime import datetime
from enum import StrEnum
from pathlib import Path

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class DispatchStatus(StrEnum):
    PREPARED = "PREPARED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    PARTIAL = "PARTIAL"


class BlockStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class Dispatch(Base):
    __tablename__ = "dispatch"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    status: Mapped[str] = mapped_column(String(20), default=DispatchStatus.PREPARED)

    create_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    execute_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    finish_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    blocks: Mapped[list["DispatchBlock"]] = relationship(
        "DispatchBlock", back_populates="dispatch", cascade="all, delete-orphan"
    )

    @property
    def included_blocks(self) -> list["DispatchBlock"]:
        return [block for block in self.blocks if block.included]

    @property
    def failed_blocks(self) -> list["DispatchBlock"]:
        return [block for block in self.included_blocks if block.status == BlockStatus.FAILED]

    @property
    def is_running(self) -> bool:
        return self.status == DispatchStatus.RUNNING


class DispatchBlock(Base):
    __tablename__ = "dispatch_block"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    dispatch_id: Mapped[int] = mapped_column(ForeignKey("dispatch.id"), nullable=False)

    prefix_name: Mapped[str] = mapped_column(String(3), nullable=False)

    intended_recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)

    file_paths: Mapped[list] = mapped_column(JSON, nullable=False)

    included: Mapped[bool] = mapped_column(Boolean, default=True)

    status: Mapped[str] = mapped_column(String(20), default=BlockStatus.PENDING)

    delivered_to: Mapped[str | None] = mapped_column(String(255), nullable=True)

    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    attempts: Mapped[int] = mapped_column(Integer, default=0)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    dispatch: Mapped["Dispatch"] = relationship("Dispatch", back_populates="blocks")

    @property
    def files(self) -> list[Path]:
        return [Path(file_path) for file_path in self.file_paths]

    @property
    def is_sendable(self) -> bool:
        return self.included and self.intended_recipient is not None and bool(self.file_paths)

    @property
    def was_sent(self) -> bool:
        return self.status == BlockStatus.SENT
