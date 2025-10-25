import asyncio
import json
import logging
from typing import Any
from collections.abc import Awaitable, Callable

from abc import abstractmethod
from enum import StrEnum, auto
from dataclasses import dataclass, field
from uuid import uuid4

from .exceptions import ErrorMessageException

logger = logging.getLogger(__name__)


class MessageType(StrEnum):
    incoming = auto()
    outgoing = auto()
    error = auto()
    response = auto()
    unknown = auto()
    deprecated = auto()


@dataclass
class ReceivedMessage:
    message_type: MessageType
    data: dict[str, Any]
    correlation_id: str | None = None


@dataclass
class BaseConnection:
    incoming_queue: asyncio.Queue[dict[str, Any] | None] = field(
        default_factory=asyncio.Queue[dict[str, Any] | None]
    )
    outgoing_queue: asyncio.Queue[dict[str, Any] | None] = field(
        default_factory=asyncio.Queue[dict[str, Any] | None]
    )
    error_queue: asyncio.Queue[dict[str, Any] | None] = field(
        default_factory=asyncio.Queue[dict[str, Any] | None]
    )
    result_queues: dict[str, asyncio.Queue[tuple[bool, dict[str, Any]] | None]] = field(
        default_factory=dict[str, asyncio.Queue[tuple[bool, dict[str, Any]] | None]]
    )

    on_disconnect: list[Callable[[], Awaitable[None]]] = field(
        default_factory=list[Callable[[], Awaitable[None]]]
    )

    echo: bool = False
    silent: bool = False

    @abstractmethod
    async def run(self):
        pass

    @abstractmethod
    async def send(
        self, topic_end: str, data: dict[str, Any], correlation_data: str | None = None
    ) -> str:
        pass

    async def handle(self, message: ReceivedMessage):
        is_error = message.message_type == MessageType.error

        if self.echo:
            logger.info(
                "%s %s %s",
                message.message_type,
                message.correlation_id,
                json.dumps(message.data, indent=2),
            )

        if is_error and not self.silent:
            logger.error("Got exception %s", json.dumps(message.data))

        if message.correlation_id in self.result_queues:
            await self.result_queues[message.correlation_id].put(
                (is_error, message.data)
            )

        if message.message_type == MessageType.incoming:
            await self.incoming_queue.put(message.data)
        elif message.message_type == MessageType.outgoing:
            await self.outgoing_queue.put(message.data)
        elif message.message_type == MessageType.error:
            await self.error_queue.put(message.data)

    async def handle_termination(self):
        for queue in [
            self.incoming_queue,
            self.outgoing_queue,
            self.error_queue,
        ] + list(self.result_queues.values()):
            await queue.put(None)

        for func in self.on_disconnect:
            await func()

    async def send_with_reply(
        self, topic_end: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        correlation_id = str(uuid4())

        self.result_queues[correlation_id] = asyncio.Queue()

        await self.send(topic_end, data, correlation_data=correlation_id)

        async with asyncio.timeout(1):
            result = await self.result_queues[correlation_id].get()
            if result is None:
                return {}
            error, result = result
        del self.result_queues[correlation_id]

        if error:
            raise ErrorMessageException(result)

        return result
