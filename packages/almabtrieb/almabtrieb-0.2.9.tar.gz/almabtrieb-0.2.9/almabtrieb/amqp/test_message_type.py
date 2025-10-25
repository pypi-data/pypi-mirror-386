import pytest
from almabtrieb.base import MessageType

from .message_type import message_type_for_routing_key, response_regex, error_regex


def test_response_regex():
    assert response_regex.match("receive.alice.response.fetch")

    assert not response_regex.match("receive.alice.incoming")
    assert not response_regex.match("receive.alice.incoming.test")

    assert error_regex.match("error.alice")


@pytest.mark.parametrize(
    "routing_key,expected",
    [
        ("receive.alice.response.fetch", MessageType.response),
        ("receive.alice.incoming", MessageType.deprecated),
        ("receive.alice.incoming.Activity", MessageType.incoming),
        ("receive.alice.outgoing", MessageType.deprecated),
        ("receive.alice.outgoing.Activity", MessageType.outgoing),
        ("error.alice", MessageType.error),
        ("unknown", MessageType.unknown),
    ],
)
def test_message_type_for_routing_key(routing_key, expected):
    result = message_type_for_routing_key(routing_key)

    assert result == expected
