from sqlalchemy.orm import Mapped, mapped_column
from model.prefix import Prefix


class UserEmail:
    __tablename__ = "user_email"

    email: Mapped[str] = mapped_column(String, primary_key=True)

    isActive: Mapped[bool] = mapped_column(Boolean)

    create_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    prefix_id: Mapped[int] = mapped_column(ForeignKey("prefix.id"), nullable=False)

    prefix: Mapped["Prefix"] = relationship("Prefix")