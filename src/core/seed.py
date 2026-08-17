from datetime import datetime

from src.core.database import SessionLocal
from src.model.prefix import Prefix
from src.model.user_email import UserEmail

BRAZILIAN_STATES = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]


def seed_prefixes(db) -> int:
    existing = {name for (name,) in db.query(Prefix.prefix_name).all()}

    created = [
        Prefix(prefix_name=uf, required_prefix=True, create_at=datetime.now())
        for uf in BRAZILIAN_STATES
        if uf not in existing
    ]

    if created:
        db.add_all(created)
        db.commit()

    return len(created)


def seed_user_emails(db) -> int:
    prefixes = db.query(Prefix).order_by(Prefix.prefix_name.asc()).all()
    existing = {prefix_id for (prefix_id,) in db.query(UserEmail.prefix_id).all()}

    created = [
        UserEmail(
            email=f"{prefix.prefix_name.lower()}@sebraeprev.com.br",
            is_active=True,
            create_at=datetime.now(),
            prefix=prefix,
        )
        for prefix in prefixes
        if prefix.id not in existing
    ]

    if created:
        db.add_all(created)
        db.commit()

    return len(created)


if __name__ == "__main__":
    db = SessionLocal()
    try:
        inserted = seed_prefixes(db)
        skipped = len(BRAZILIAN_STATES) - inserted
        print(f"{inserted} prefixo(s) inserido(s), {skipped} já existia(m).")

        inserted_emails = seed_user_emails(db)
        print(f"{inserted_emails} email(s) inserido(s).")
    finally:
        db.close()
