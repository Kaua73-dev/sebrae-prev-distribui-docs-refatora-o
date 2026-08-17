from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi_utils.cbv import cbv

from src.core.dependencies import get_dispatch_service
from src.schema.request.dispatch import DispatchBlockUpdateRequest
from src.schema.response.dispatch import DispatchResponse, DispatchStatusResponse
from src.service.dispatch import DispatchService, send_dispatch

ACCEPTED = 202

router = APIRouter(prefix="/dispatch", tags=["Dispatch"])
@cbv(router)
class DispatchController:

    service: DispatchService = Depends(get_dispatch_service)


    @router.get("/{dispatch_id}", response_model=DispatchResponse)
    def find_dispatch(self, dispatch_id: int) -> DispatchResponse:
        return self.service.find_dispatch(dispatch_id)

    @router.patch("/{dispatch_id}/block/{block_id}", response_model=DispatchResponse)
    def update_block(self, dispatch_id: int, block_id: int, request: DispatchBlockUpdateRequest) -> DispatchResponse:
        return self.service.update_block(dispatch_id, block_id, request)

    @router.post("/{dispatch_id}/execute", response_model=DispatchResponse, status_code=ACCEPTED)
    def execute(self, dispatch_id: int, background_tasks: BackgroundTasks) -> DispatchResponse:
        dispatch = self.service.lock_for_execution(dispatch_id)

        background_tasks.add_task(send_dispatch, dispatch_id)
        return dispatch

    @router.get("/{dispatch_id}/status", response_model=DispatchStatusResponse)
    def find_status(self, dispatch_id: int) -> DispatchStatusResponse:
        return self.service.find_status(dispatch_id)
