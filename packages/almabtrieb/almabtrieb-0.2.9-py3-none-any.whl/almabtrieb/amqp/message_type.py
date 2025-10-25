import logging
import re
from almabtrieb.base import MessageType

logger = logging.getLogger(__name__)

response_regex = re.compile(r"^receive.\w+\.response\.\w+$")
incoming_regex = re.compile(r"^receive.\w+\.incoming\.\w+$")
outgoing_regex = re.compile(r"^receive.\w+\.outgoing\.\w+$")
deprecated_regex = re.compile(r"^receive.\w+\.(?:outgoing|incoming)$")
error_regex = re.compile(r"^error.\w+$")


def message_type_for_routing_key(routing_key: str):
    if response_regex.match(routing_key):
        return MessageType.response
    if incoming_regex.match(routing_key):
        return MessageType.incoming
    if outgoing_regex.match(routing_key):
        return MessageType.outgoing
    if error_regex.match(routing_key):
        return MessageType.error
    if deprecated_regex.match(routing_key):
        return MessageType.deprecated

    logger.info("Unknown routing key %s", routing_key)
    return MessageType.unknown
