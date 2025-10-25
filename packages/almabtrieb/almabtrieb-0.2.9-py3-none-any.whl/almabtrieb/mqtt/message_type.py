import logging

try:
    from aiomqtt import Topic  # type: ignore
except ImportError:

    class Topic:
        def matches(self, str): ...


from almabtrieb.base import MessageType

logger = logging.getLogger(__name__)


def message_type_from_topic(topic: Topic):
    if topic.matches("receive/+/response/+"):
        return MessageType.response
    if topic.matches("receive/+/incoming/+"):
        return MessageType.incoming
    if topic.matches("receive/+/outgoing/+"):
        return MessageType.outgoing
    if topic.matches("error/+"):
        return MessageType.error

    if topic.matches("receive/+/incoming") or topic.matches("receive/+/outgoing"):
        return MessageType.deprecated

    logger.warning("Unknown topic: %s", topic)
    return MessageType.unknown
