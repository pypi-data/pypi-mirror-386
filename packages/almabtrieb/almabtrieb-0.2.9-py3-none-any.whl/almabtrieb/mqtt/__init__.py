import json
import logging
from typing import Any

try:
    from aiomqtt import Message  # type: ignore
except ImportError:

    class Message:
        payload: Any
        properties: Any
        topic: Any


from almabtrieb.mqtt.message_type import message_type_from_topic
from almabtrieb.util import parse_connection_string
from almabtrieb.base import BaseConnection, ReceivedMessage, MessageType

from .base import MqttBaseConnection

logger = logging.getLogger(__name__)


class MqttConnection(BaseConnection):
    def __init__(
        self,
        base_connection: MqttBaseConnection,
        username: str,
        echo: bool = False,
        silent: bool = False,
    ):
        super().__init__(echo=echo, silent=silent)  # type: ignore
        self.username = username
        self.base_connection = base_connection

    @staticmethod
    def from_connection_string(
        connection_string: str, echo: bool = False, silent: bool = False
    ) -> "MqttConnection":
        parsed = parse_connection_string(connection_string)
        return MqttConnection(
            base_connection=MqttBaseConnection(**parsed, echo=echo),  # type: ignore
            echo=echo,
            username=parsed.get("username"),  # type: ignore
            silent=silent,
        )

    @property
    def connected(self):
        return self.base_connection.connected

    @property
    def receive(self):
        return f"receive/{self.username}/#"

    @property
    def receive_error(self):
        return f"error/{self.username}"

    @property
    def send_topic(self):
        return f"send/{self.username}"

    async def run(self):
        try:
            async with self.base_connection.run(
                [self.receive, self.receive_error]
            ) as client:
                try:
                    async for message in client.messages:
                        await self.handle_message(message)
                except Exception:
                    logger.warning("Mesage processing stopped")

        except Exception:
            logger.warning("Sending termination to listeners")
            await self.handle_termination()

    async def send(
        self, topic_end: str, data: dict[str, Any], correlation_data: str | None = None
    ) -> str:
        topic = f"{self.send_topic}/{topic_end}"

        correlation_data = await self.base_connection.send(
            topic, data, correlation_data=correlation_data
        )

        return correlation_data

    async def handle_message(self, message):
        correlation_id = getattr(message.properties, "CorrelationData").decode()
        payload = message.payload
        if (
            payload is None
            or isinstance(payload, int)
            or isinstance(payload, float)
            or isinstance(payload, bytearray)
        ):
            try:
                logger.warning("Cannot handle payload %s", payload)
            except Exception:
                logger.warning("cannot handle payload")
            return

        message_type = message_type_from_topic(message.topic)

        if message_type == MessageType.deprecated:
            return

        await self.handle(
            ReceivedMessage(
                message_type=message_type,
                correlation_id=correlation_id,
                data=json.loads(payload),
            ),
        )
