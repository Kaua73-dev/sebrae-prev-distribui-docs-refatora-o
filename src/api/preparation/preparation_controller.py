from fastapi import APIRouter, Depends
from fastapi_utils.cbv import cbv

from src.service.preparation.file_block import FileBlock
from src.core.dependencies import get_preparation_service
from src.service.preparation.preparation_service import PreparationService

router = APIRouter(tags=["Preparation"])
@cbv(router)
class PreparationController:

    service: PreparationService = Depends(get_preparation_service)


    @router.post("/start", response_model=list[FileBlock])
    def start(self):
        return self.service.mount_block_files()
