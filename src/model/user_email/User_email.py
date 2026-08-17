from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.model.prefix import Prefix


class UserEmail(Base):
    __tablename__ = "user_emails"
    __table_args__ = (UniqueConstraint("email", name="uk_user_email"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    create_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    prefix_id: Mapped[int] = mapped_column(ForeignKey("prefix.id"), nullable=False)

    prefix: Mapped["Prefix"] = relationship("Prefix")
