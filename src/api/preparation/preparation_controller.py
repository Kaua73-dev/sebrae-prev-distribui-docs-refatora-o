from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from src.core.dependencies import get_dispatch_service, get_preparation_service
from src.schema.response.dispatch import DispatchResponse
from src.service.dispatch import DispatchService
from src.service.preparation.file_block import FileBlock
from src.service.preparation.preparation_service import PreparationService

router = APIRouter(tags=["Preparation"])
@cbv(router)
class PreparationController:

    service: PreparationService = Depends(get_preparation_service)
    dispatch_service: DispatchService = Depends(get_dispatch_service)


    @router.post("/start", response_model=DispatchResponse)
    def start(self) -> DispatchResponse:
        return self.dispatch_service.prepare()

    @router.get("/preview", response_model=list[FileBlock])
    def preview(self) -> list[FileBlock]:
        return self.service.mount_block_files()
