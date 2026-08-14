from fastapi import APIRouter, Depends

from src.core.dependencies import get_prefix_service
from src.schema.request.prefix import PrefixRequest
from src.schema.request.prefix.prefix_update_request import PrefixUpdateRequest
from src.schema.response.prefix import PrefixResponse
from src.service.prefix.prefix_service import PrefixService
from fastapi_utils.cbv import cbv


router = APIRouter(prefix="/prefixes", tags=["Prefixes"])
@cbv(router)
class PrefixController:

    service: PrefixService = Depends(get_prefix_service)


    @router.post("/create", response_model=PrefixResponse)
    def create_prefix(self, request: PrefixRequest) -> PrefixResponse:
        return self.service.create_prefix(request)

    @router.put("/update", response_model=PrefixResponse)
    def update_prefix(self, request: PrefixUpdateRequest) -> PrefixResponse:
        return self.service.update_prefix(request)

    @router.get("/all", response_model= list[PrefixResponse])
    def find_all_prefixes(self) -> list[PrefixResponse]:
        return self.service.find_all_prefixes()

    @router.get("/required", response_model=PrefixResponse)
    def find_prefix_required_true(self) -> list[PrefixResponse]:
        return self.service.find_prefix_required_true()