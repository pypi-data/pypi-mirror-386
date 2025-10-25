import pytest

from unittest.mock import MagicMock

from . import AmqpConnection


def is_aio_pika_installed():
    try:
        import aio_pika  # noqa

        return True
    except ImportError:
        return False


@pytest.mark.skipif(not is_aio_pika_installed(), reason="aiopoka not installed")
def test_connected():
    connection = AmqpConnection(MagicMock(), "name")

    assert not connection.connected
