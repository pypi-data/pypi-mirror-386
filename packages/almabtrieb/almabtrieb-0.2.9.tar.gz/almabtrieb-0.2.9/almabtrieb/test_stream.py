import asyncio

import pytest

from almabtrieb.stream import Stream, StreamNoNewItemException


async def test_stream_quits():
    queue = asyncio.Queue[str | None]()

    stream = Stream[str](queue)
    await queue.put(None)

    async for _ in stream:
        ...


async def test_stream_returns_values():
    queue = asyncio.Queue[str | None]()

    stream = Stream(queue)
    await queue.put("one")
    await queue.put("two")
    await queue.put(None)

    result: list[str] = []

    async for x in stream:
        result.append(x)

    assert result == ["one", "two"]


async def test_stream_next():
    queue = asyncio.Queue[str | None]()

    stream = Stream(queue)
    await queue.put("one")
    await queue.put("two")
    await queue.put(None)

    result = await stream.next()

    assert result == "one"


async def test_stream_next_handles_timeout():
    queue = asyncio.Queue[str | None]()

    stream = Stream(queue)

    with pytest.raises(StreamNoNewItemException):
        await stream.next(timeout=0.1)


async def test_stream_clear():
    queue = asyncio.Queue[str | None]()

    stream = Stream(queue)
    await queue.put("one")
    await queue.put("two")

    await stream.clear()

    await queue.put(None)

    result = await stream.next()

    assert result is None
