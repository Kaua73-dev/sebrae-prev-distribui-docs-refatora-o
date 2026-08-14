from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from service.preparation.file_block import FileBlock
from src.core.dependencies import get_preparation_service
from service.preparation.preparation_service import PreparationService

router = APIRouter(prefix="/start", tags=["Prefixes"])
@cbv(router)
class PreparationController:

    service: PreparationService = Depends(get_preparation_service)


    @router.post("", response_model=list[FileBlock])
    def start(self):
        return self.service.mount_block_files()
