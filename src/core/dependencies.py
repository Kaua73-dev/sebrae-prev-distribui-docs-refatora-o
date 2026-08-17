from fastapi import Depends
from sqlalchemy.orm.session import Session

from src.core.database import get_db
from src.repository.dispatch import DispatchRepository
from src.repository.prefix import PrefixRepository
from src.repository.user_email import UserEmailRepository
from src.service.dispatch import DispatchService
from src.service.prefix.prefix_service import PrefixService
from src.service.preparation.preparation_service import PreparationService
from src.service.user_email import UserEmailService


def get_prefix_service(db: Session = Depends(get_db)) -> PrefixService:
    return PrefixService(PrefixRepository(db), db)

def get_user_email_service(db: Session = Depends(get_db)) -> UserEmailService:
    return UserEmailService(UserEmailRepository(db), PrefixRepository(db), db)

def get_preparation_service(
    prefix_service: PrefixService = Depends(get_prefix_service),
    db: Session = Depends(get_db),
) -> PreparationService:
    return PreparationService(prefix_service, UserEmailRepository(db))

def get_dispatch_service(
    preparation_service: PreparationService = Depends(get_preparation_service),
    db: Session = Depends(get_db),
) -> DispatchService:
    return DispatchService(DispatchRepository(db), preparation_service, db)
