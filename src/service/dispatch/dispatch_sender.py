from datetime import datetime
from typing import Any, Callable

from starlette.concurrency import run_in_threadpool

from src.core.database import new_session
from src.model.dispatch import BlockStatus, Dispatch, DispatchBlock, DispatchStatus
from src.repository.dispatch import DispatchRepository
from src.service.mail import MailService

MAX_ERROR_LENGTH = 2000


class DispatchSender:

    def __init__(self, mail_service: MailService | None = None):
        self.mail_service = mail_service or MailService()

    async def send(self, dispatch_id: int) -> None:
        with new_session() as session:
            repository = DispatchRepository(session)

            for block in await self._in_database(repository.find_blocks_to_send, dispatch_id):
                await self._send_block(block)
                await self._in_database(repository.save_block, block)

            await self._finish(repository, dispatch_id)

    async def _send_block(self, block: DispatchBlock) -> None:
        if not block.is_sendable:
            return

        block.attempts += 1

        try:
            block.delivered_to = await self.mail_service.send_files(
                block.prefix_name, block.intended_recipient, block.files
            )
            block.status = BlockStatus.SENT
            block.delivered_at = datetime.now()
            block.error = None
        except Exception as error:
            block.status = BlockStatus.FAILED
            block.error = self._describe(error)

    async def _finish(self, repository: DispatchRepository, dispatch_id: int) -> None:
        dispatch = await self._in_database(repository.find_by_id, dispatch_id)

        if dispatch is None:
            return

        dispatch.status = self._final_status(dispatch)
        dispatch.finish_at = datetime.now()

        await self._in_database(repository.save, dispatch)

    @staticmethod
    def _final_status(dispatch: Dispatch) -> DispatchStatus:
        if dispatch.failed_blocks:
            return DispatchStatus.PARTIAL
        return DispatchStatus.DONE

    @staticmethod
    def _describe(error: Exception) -> str:
        return f"{type(error).__name__}: {error}"[:MAX_ERROR_LENGTH]

    @staticmethod
    async def _in_database(operation: Callable[..., Any], *args: Any) -> Any:
        return await run_in_threadpool(operation, *args)


async def send_dispatch(dispatch_id: int) -> None:
    await DispatchSender().send(dispatch_id)
