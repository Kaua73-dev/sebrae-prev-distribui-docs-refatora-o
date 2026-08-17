from sqlalchemy.orm import Session
from src.model.user_email.User_email import UserEmail


class UserEmailRepository:

    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[UserEmail]:
        return self.db.query(UserEmail).all()

    def save(self, prefix: UserEmail) -> UserEmail:
        self.db.add(prefix)
        self.db.commit()
        self.db.refresh(prefix)
        return prefix

    def find_by_is_active_true(self) -> list[UserEmail]:
        return (
            self.db.query(UserEmail)
            .filter(UserEmail.isActive.is_(True))
            .all()
        )