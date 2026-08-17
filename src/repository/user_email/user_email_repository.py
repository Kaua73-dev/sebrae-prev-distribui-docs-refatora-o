from sqlalchemy.orm import Session, joinedload

from src.model.user_email import UserEmail


class UserEmailRepository:

    def __init__(self, db: Session):
        self.db = db

    def find_all(self) -> list[UserEmail]:
        return self.db.query(UserEmail).all()

    def find_all_with_prefix(self) -> list[UserEmail]:
        return (
            self.db.query(UserEmail)
            .options(joinedload(UserEmail.prefix))
            .all()
        )

    def save(self, user_email: UserEmail) -> UserEmail:
        self.db.add(user_email)
        self.db.commit()
        self.db.refresh(user_email)
        return user_email

    def find_by_is_active_true(self) -> list[UserEmail]:
        return (
            self.db.query(UserEmail)
            .options(joinedload(UserEmail.prefix))
            .filter(UserEmail.is_active.is_(True))
            .all()
        )

    def find_by_id(self, user_email_id: int) -> UserEmail | None:
        return (
            self.db.query(UserEmail)
            .options(joinedload(UserEmail.prefix))
            .filter(UserEmail.id == user_email_id)
            .first()
        )

    def find_by_email(self, email: str) -> UserEmail | None:
        return (
            self.db.query(UserEmail)
            .filter(UserEmail.email == email)
            .first()
        )

    def delete(self, user_email: UserEmail) -> None:
        self.db.delete(user_email)
        self.db.commit()
