from fastapi import Depends
from sqlalchemy.orm.session import Session

from service.preparation.preparation_service import PreparationService
from src.core.database import get_db
from src.repository.prefix import PrefixRepository
from src.service.prefix.prefix_service import PrefixService


def get_prefix_service(db: Session = Depends(get_db)) -> PrefixService:
    repository = PrefixRepository(db)
    return PrefixService(repository, db)

def get_preparation_service(
    prefix_service: PrefixService = Depends(get_prefix_service),
) -> PreparationService:
    return PreparationService(prefix_service)