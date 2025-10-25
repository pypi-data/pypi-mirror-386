import asyncio
from dataclasses import dataclass
from typing import Generic, TypeVar


class StreamNoNewItemException(Exception):
    """Raised if no new item is present in stream"""

    ...


T = TypeVar("T")


@dataclass
class Stream(Generic[T]):
    """Transforms an asyncio.Queue into an asynchronous iterator with two helper function

    Usage
    ```python
    queue = asyncio.Queue()
    async for x in Stream(queue):
        await do_something_with(x)
    ```
    """

    queue: asyncio.Queue[T | None]

    def __aiter__(self):
        return self

    async def next(self, timeout: float = 1) -> T | None:
        """The next element, if the wait time is longer than timeout, an
        [almabtrieb.stream.StreamNoNewItemException][] is raised."""
        try:
            async with asyncio.timeout(timeout):
                return await self.queue.get()
        except asyncio.TimeoutError:
            raise StreamNoNewItemException("No new message in stream")

    async def __anext__(self) -> T:
        result = await self.queue.get()
        if result is None:
            raise StopAsyncIteration()

        return result

    async def clear(self):
        """Removes all items from the queue"""
        while not self.queue.empty():
            await self.queue.get()
