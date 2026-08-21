"""
Cria a tabela users e um admin.

Necessario porque register e protegido por ROLE ADMIN: sem um admin no banco nao
existe ninguem que possa registrar o primeiro usuario. Este script e a unica porta
de entrada, e roda fora da API de proposito.

Uso preferido — a senha nao fica gravada em disco:

    python -m scripts.seed_admin --name "Nome" --email a@b.com --password SENHA

Alternativa por ambiente, para automacao (ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD).
Atencao: pydantic-settings le o .env para dentro do Settings, mas NAO exporta nada
para os.environ. Por isso o load_dotenv abaixo e necessario para que colocar essas
variaveis no .env realmente funcione.

Rodar de novo com um email que ja existe nao faz nada — e seguro repetir.
"""

import argparse
import os
import sys

from dotenv import load_dotenv

from src.core.database import SessionLocal, engine
from src.core.security import hash_password
from src.model.user import User, UserRole
from src.schema.request.user import MIN_PASSWORD_LENGTH

load_dotenv()

DEFAULT_NAME = "Administrador"


def create_users_table() -> None:
    # Apenas a tabela de users. O projeto nao usa create_all nem Alembic, entao nao
    # e papel deste script mexer no schema das outras tabelas.
    User.__table__.create(engine, checkfirst=True)


def read_admin() -> tuple[str, str, str]:
    parser = argparse.ArgumentParser(description="Cria um usuario ADMIN.")
    parser.add_argument("--name", default=None)
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default=None)
    arguments = parser.parse_args()

    name = (arguments.name or os.environ.get("ADMIN_NAME") or DEFAULT_NAME).strip()
    email = (arguments.email or os.environ.get("ADMIN_EMAIL") or "").strip().lower()
    password = arguments.password or os.environ.get("ADMIN_PASSWORD") or ""

    if not email or not password:
        sys.exit("Informe --email e --password (ou ADMIN_EMAIL e ADMIN_PASSWORD no ambiente).")

    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"A senha precisa de pelo menos {MIN_PASSWORD_LENGTH} caracteres.")

    return name, email, password


def seed_admin(db, name: str, email: str, password: str) -> bool:
    if db.query(User).filter(User.email == email).first() is not None:
        return False

    db.add(
        User(
            name=name,
            email=email,
            password=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
    )
    db.commit()

    return True


if __name__ == "__main__":
    admin_name, admin_email, admin_password = read_admin()

    create_users_table()
    print("Tabela users verificada.")

    db = SessionLocal()
    try:
        if seed_admin(db, admin_name, admin_email, admin_password):
            print(f"Admin criado: {admin_email}")
        else:
            print(f"Admin {admin_email} ja existia, nada foi alterado.")
    finally:
        db.close()
