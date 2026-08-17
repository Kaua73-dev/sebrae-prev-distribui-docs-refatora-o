from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from src.core.config import settings
from src.exception.dispatch import (DispatchAlreadyRunningException,DispatchBlockNotFoundException,DispatchNotFoundException,DispatchNothingToSendException)
from src.model.dispatch import BlockStatus, Dispatch, DispatchBlock, DispatchStatus
from src.repository.dispatch import DispatchRepository
from src.schema.request.dispatch import DispatchBlockUpdateRequest
from src.schema.response.dispatch import DispatchResponse, DispatchStatusResponse
from src.service.dispatch.pre_flight_check import PreFlightCheck
from src.service.preparation.file_block import FileBlock
from src.service.preparation.preparation_service import PreparationService


class DispatchService:


    def __init__(self, dispatch_repository: DispatchRepository, preparation_service: PreparationService, session: Session):
        self.dispatch_repository = dispatch_repository
        self.preparation_service = preparation_service
        self.session = session




    def prepare(self) -> DispatchResponse:
        file_blocks = self.preparation_service.mount_block_files()
        files_without_prefix = self.preparation_service.find_files_without_prefix(file_blocks)

        dispatch = Dispatch()
        dispatch.status = DispatchStatus.PREPARED
        dispatch.create_at = datetime.now()
        dispatch.blocks = [self._to_block(file_block) for file_block in file_blocks]

        self.dispatch_repository.save(dispatch)

        return self._to_response(dispatch, files_without_prefix)

    def find_dispatch(self, dispatch_id: int) -> DispatchResponse:
        return self._to_response(self._get_dispatch(dispatch_id))

    def update_block(self, dispatch_id: int, block_id: int, request: DispatchBlockUpdateRequest) -> DispatchResponse:
        dispatch = self._get_dispatch(dispatch_id)

        if dispatch.is_running:
            raise DispatchAlreadyRunningException()

        block = self._get_block(dispatch, block_id)

        if request.included is not None:
            block.included = request.included

        if request.email is not None:
            block.intended_recipient = request.email.strip().lower()

        self.dispatch_repository.save_block(block)

        return self._to_response(self._get_dispatch(dispatch_id))

    def lock_for_execution(self, dispatch_id: int) -> DispatchResponse:
        dispatch = self._get_dispatch(dispatch_id)

        if dispatch.is_running:
            raise DispatchAlreadyRunningException()

        if not self._sendable_blocks(dispatch_id):
            raise DispatchNothingToSendException()

        dispatch.status = DispatchStatus.RUNNING
        dispatch.execute_at = datetime.now()
        dispatch.finish_at = None

        self.dispatch_repository.save(dispatch)

        return self._to_response(dispatch)

    def find_status(self, dispatch_id: int) -> DispatchStatusResponse:
        dispatch = self._get_dispatch(dispatch_id)
        included = dispatch.included_blocks

        return DispatchStatusResponse(
            id=dispatch.id,
            status=dispatch.status,
            total=len(included),
            sent=self._count(included, BlockStatus.SENT),
            failed=self._count(included, BlockStatus.FAILED),
            pending=self._count(included, BlockStatus.PENDING),
            excluded=len(dispatch.blocks) - len(included),
        )




    @staticmethod
    def _to_block(file_block: FileBlock) -> DispatchBlock:
        return DispatchBlock(
            prefix_name=file_block.prefix,
            intended_recipient=file_block.email,
            file_paths=[str(file) for file in file_block.files],
            included=file_block.email is not None and bool(file_block.files),
            status=BlockStatus.PENDING,
            attempts=0,
        )

    @staticmethod
    def _to_response(dispatch: Dispatch, files_without_prefix: list[Path] | None = None) -> DispatchResponse:
        return DispatchResponse(
            id=dispatch.id,
            status=dispatch.status,
            create_at=dispatch.create_at,
            execute_at=dispatch.execute_at,
            finish_at=dispatch.finish_at,
            blocks=sorted(dispatch.blocks, key=lambda block: block.prefix_name),
            warnings=PreFlightCheck(dispatch, files_without_prefix).warnings(),
            mail_sending_disabled=settings.MAIL_SENDING_DISABLED,
            mail_redirected_to=settings.MAIL_REDIRECT_ALL_TO or None,
        )

    @staticmethod
    def _count(blocks: list[DispatchBlock], status: BlockStatus) -> int:
        return len([block for block in blocks if block.status == status])

    def _sendable_blocks(self, dispatch_id: int) -> list[DispatchBlock]:
        return [
            block
            for block in self.dispatch_repository.find_blocks_to_send(dispatch_id)
            if block.is_sendable
        ]

    def _get_dispatch(self, dispatch_id: int) -> Dispatch:
        dispatch = self.dispatch_repository.find_by_id(dispatch_id)

        if dispatch is None:
            raise DispatchNotFoundException()

        return dispatch

    @staticmethod
    def _get_block(dispatch: Dispatch, block_id: int) -> DispatchBlock:
        block = next((block for block in dispatch.blocks if block.id == block_id), None)

        if block is None:
            raise DispatchBlockNotFoundException()

        return block
