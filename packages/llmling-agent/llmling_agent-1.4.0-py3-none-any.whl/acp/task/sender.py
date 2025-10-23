"""Sender class for sending messages to a remote peer."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import contextlib
from dataclasses import dataclass
import json
import logging
from typing import Any

from .supervisor import TaskSupervisor


__all__ = ["MessageSender", "SenderFactory"]


SenderFactory = Callable[[asyncio.StreamWriter, TaskSupervisor], "MessageSender"]


@dataclass(slots=True)
class _PendingSend:
    payload: bytes
    future: asyncio.Future[None]


class MessageSender:
    """Async message sender that queues and transmits JSON-RPC messages."""

    def __init__(
        self,
        writer: asyncio.StreamWriter,
        supervisor: TaskSupervisor,
    ) -> None:
        self._writer = writer
        self._queue: asyncio.Queue[_PendingSend | None] = asyncio.Queue()
        self._closed = False
        self._task = supervisor.create(
            self._loop(), name="acp.Sender.loop", on_error=self._on_error
        )

    async def send(self, payload: dict[str, Any]) -> None:
        data = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        future: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        await self._queue.put(_PendingSend(data, future))
        await future

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._queue.put(None)
        if self._task is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _loop(self) -> None:
        try:
            while True:
                item = await self._queue.get()
                if item is None:
                    return
                try:
                    self._writer.write(item.payload)
                    await self._writer.drain()
                except Exception as exc:
                    if not item.future.done():
                        item.future.set_exception(exc)
                    raise
                else:
                    if not item.future.done():
                        item.future.set_result(None)
        except asyncio.CancelledError:
            return

    def _on_error(self, task: asyncio.Task[Any], exc: BaseException) -> None:
        logging.exception("Send loop failed", exc_info=exc)
