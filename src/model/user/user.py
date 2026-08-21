from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uk_user_login_email"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(120), nullable=False)

    email: Mapped[str] = mapped_column(String(255), nullable=False)

    password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    create_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
