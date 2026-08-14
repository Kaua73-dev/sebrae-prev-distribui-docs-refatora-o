from sqlalchemy.orm import Session

from src.exception.prefix.prefix_exceptions import PrefixAlreadyExistException, PrefixNotFoundException
from src.model.prefix import Prefix
from src.repository.prefix import PrefixRepository
from src.schema.request.prefix import PrefixRequest
from src.schema.request.prefix.prefix_update_request import PrefixUpdateRequest
from src.schema.response.prefix import PrefixResponse
from datetime import datetime

class PrefixService:
    
    
    def __init__(self, prefix_repository: PrefixRepository, session: Session):
        self.prefix_repository = prefix_repository
        self.session = session

    @staticmethod
    def _normalize_prefix(prefix: str ) -> str:
        return prefix.strip().upper()

    @staticmethod
    def _to_response(prefix: Prefix) -> PrefixResponse:
        return PrefixResponse.model_validate(prefix)


    def create_prefix(self, request: PrefixRequest) -> PrefixResponse:

        if request.prefix_name is None or request.prefix_name == "":
            raise ValueError("prefix is required")

        normalized_prefix_name = self._normalize_prefix(request.prefix_name)

        if self.prefix_repository.find_by_prefix_name(normalized_prefix_name):
            raise PrefixAlreadyExistException()

        prefix = Prefix()
        prefix.prefix_name = normalized_prefix_name
        prefix.required_prefix = True
        prefix.create_at = datetime.now()

        self.prefix_repository.save(prefix)

        return self._to_response(prefix)

    def update_prefix(self, request: PrefixUpdateRequest) -> PrefixResponse:

        if request.prefix_name is None or request.prefix_name == "":
            raise ValueError("prefix is required")

        with self.session.begin():
         prefix = self.prefix_repository.find_by_prefix_name(self._normalize_prefix(request.prefix_name))

        if prefix is None:
            raise PrefixNotFoundException()

        prefix.required_prefix = request.prefix_required

        self.prefix_repository.save(prefix)

        return self._to_response(prefix)

    def find_all_prefixes(self) -> list[PrefixResponse]:
        return list(map(self._to_response, self.prefix_repository.find_all()))

    def find_prefix_required_true(self) -> list[PrefixResponse]:
        return list(map(self._to_response, self.prefix_repository.find_by_required_prefix_true_order_by_name()))












