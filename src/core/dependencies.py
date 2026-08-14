from fastapi import Depends
from sqlalchemy.orm.session import Session

from src.core.database import get_db
from src.repository.prefix import PrefixRepository
from src.service.prefix.prefix_service import PrefixService


def get_prefix_service(db: Session = Depends(get_db)) -> PrefixService:
    repository = PrefixRepository(db)
    return PrefixService(repository, db)