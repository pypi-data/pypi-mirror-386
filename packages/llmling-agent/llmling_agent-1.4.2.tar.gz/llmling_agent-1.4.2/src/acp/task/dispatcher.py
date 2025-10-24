"""Message dispatcher for ACP tasks."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Protocol

from acp.task import RpcTaskKind


if TYPE_CHECKING:
    from acp.task.queue import MessageQueue
    from acp.task.state import MessageStateStore
    from acp.task.supervisor import TaskSupervisor


RequestRunner = Callable[[dict[str, Any]], Awaitable[Any]]
NotificationRunner = Callable[[dict[str, Any]], Awaitable[None]]


class MessageDispatcher(Protocol):
    """Protocol for message dispatchers."""

    def start(self) -> None: ...

    async def stop(self) -> None: ...


class DefaultMessageDispatcher(MessageDispatcher):
    """Background worker that consumes RPC tasks from a broker."""

    def __init__(
        self,
        *,
        queue: MessageQueue,
        supervisor: TaskSupervisor,
        store: MessageStateStore,
        request_runner: RequestRunner,
        notification_runner: NotificationRunner,
    ) -> None:
        self._queue = queue
        self._supervisor = supervisor
        self._store = store
        self._request_runner = request_runner
        self._notification_runner = notification_runner
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is not None:
            msg = "dispatcher already started"
            raise RuntimeError(msg)
        self._task = self._supervisor.create(self._run(), name="acp.Dispatcher.loop")

    async def _run(self) -> None:
        try:
            async for task in self._queue:
                try:
                    if task.kind is RpcTaskKind.REQUEST:
                        await self._dispatch_request(task.message)
                    else:
                        await self._dispatch_notification(task.message)
                finally:
                    self._queue.task_done()
        except asyncio.CancelledError:
            return

    async def stop(self) -> None:
        await self._queue.close()
        if self._task is not None:
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _dispatch_request(self, msg: dict[str, Any]) -> None:
        record = self._store.begin_incoming(msg.get("method", ""), msg.get("params"))

        async def runner() -> None:
            try:
                result = await self._request_runner(msg)
            except Exception as exc:
                self._store.fail_incoming(record, exc)
                raise
            else:
                self._store.complete_incoming(record, result)

        self._supervisor.create(runner(), name="acp.Dispatcher.request")

    async def _dispatch_notification(self, message: dict[str, Any]) -> None:
        async def runner() -> None:
            await self._notification_runner(message)

        self._supervisor.create(runner(), name="acp.Dispatcher.notification")
