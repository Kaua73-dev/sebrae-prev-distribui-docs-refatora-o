from datetime import datetime

from src.core.database import SessionLocal
from src.model.prefix import Prefix

# 26 estados + Distrito Federal
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


if __name__ == "__main__":
    db = SessionLocal()
    try:
        inserted = seed_prefixes(db)
        skipped = len(BRAZILIAN_STATES) - inserted
        print(f"{inserted} prefixo(s) inserido(s), {skipped} já existia(m).")
    finally:
        db.close()
