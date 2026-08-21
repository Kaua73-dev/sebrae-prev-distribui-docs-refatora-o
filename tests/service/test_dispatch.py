from datetime import datetime

import pytest

from src.exception.dispatch import (
    DispatchAlreadyRunningException,
    DispatchNotFoundException,
    DispatchNothingToSendException,
)
from src.model.dispatch import BlockStatus, Dispatch, DispatchBlock, DispatchStatus


def create_block(block_id: int = 1, recipient: str | None = "bsb@sebraeprev.com.br", included: bool = True, file_paths: list[str] | None = None) -> DispatchBlock:
    block = DispatchBlock()
    block.id = block_id
    block.prefix_name = "BSB"
    block.intended_recipient = recipient
    block.file_paths = file_paths if file_paths is not None else ["C:/arquivos/BSB_001.pdf"]
    block.included = included
    block.status = BlockStatus.PENDING
    block.delivered_to = None
    block.delivered_at = None
    block.attempts = 0
    block.error = None

    return block


def create_dispatch(status: str = DispatchStatus.PREPARED, blocks: list[DispatchBlock] | None = None) -> Dispatch:
    dispatch = Dispatch()
    dispatch.id = 1
    dispatch.status = status
    dispatch.create_at = datetime.now()
    dispatch.execute_at = None
    dispatch.finish_at = None
    dispatch.blocks = blocks if blocks is not None else [create_block()]

    return dispatch


class TestDispatchService:


    @pytest.mark.parametrize(
        "recipient, included, file_paths, expected",
        [
            ("bsb@sebraeprev.com.br", True, ["BSB_001.pdf"], True),
            (None, True, ["BSB_001.pdf"], False),
            ("bsb@sebraeprev.com.br", False, ["BSB_001.pdf"], False),
            ("bsb@sebraeprev.com.br", True, [], False),
        ],
    )
    def test_block_is_sendable_only_with_recipient_and_files(self, recipient, included, file_paths, expected):
        block = create_block(recipient=recipient, included=included, file_paths=file_paths)

        assert block.is_sendable is expected

    def test_lock_for_execution_with_success(self, dispatch_service, dispatch_repository_mock):

        dispatch = create_dispatch()
        dispatch.finish_at = datetime.now()

        dispatch_repository_mock.find_by_id.return_value = dispatch
        dispatch_repository_mock.find_blocks_to_send.return_value = dispatch.blocks

        response = dispatch_service.lock_for_execution(1)

        assert dispatch.status == DispatchStatus.RUNNING
        assert dispatch.execute_at is not None
        assert dispatch.finish_at is None

        assert response.status == DispatchStatus.RUNNING
        assert len(response.blocks) == 1

        dispatch_repository_mock.find_by_id.assert_called_once_with(1)
        dispatch_repository_mock.save.assert_called_once_with(dispatch)

    def test_lock_for_execution_when_already_running_throws_exception(self, dispatch_service, dispatch_repository_mock):

        dispatch = create_dispatch(status=DispatchStatus.RUNNING)

        dispatch_repository_mock.find_by_id.return_value = dispatch
        dispatch_repository_mock.find_blocks_to_send.return_value = dispatch.blocks

        with pytest.raises(DispatchAlreadyRunningException):
            dispatch_service.lock_for_execution(1)


        # A guarda tem que barrar antes de consultar os blocos.
        dispatch_repository_mock.find_blocks_to_send.assert_not_called()
        dispatch_repository_mock.save.assert_not_called()

    def test_lock_for_execution_without_sendable_blocks_throws_exception(self, dispatch_service, dispatch_repository_mock):

        dispatch = create_dispatch()

        dispatch_repository_mock.find_by_id.return_value = dispatch
        dispatch_repository_mock.find_blocks_to_send.return_value = [create_block(recipient=None)]

        with pytest.raises(DispatchNothingToSendException):
            dispatch_service.lock_for_execution(1)


        assert dispatch.status == DispatchStatus.PREPARED
        dispatch_repository_mock.save.assert_not_called()

    def test_lock_for_execution_not_found_throws_exception(self, dispatch_service, dispatch_repository_mock):

        dispatch_repository_mock.find_by_id.return_value = None

        with pytest.raises(DispatchNotFoundException):
            dispatch_service.lock_for_execution(99)


        dispatch_repository_mock.find_by_id.assert_called_once_with(99)
        dispatch_repository_mock.save.assert_not_called()
