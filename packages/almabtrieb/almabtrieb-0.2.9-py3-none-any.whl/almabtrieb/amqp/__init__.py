from typing import Any
from uuid import uuid4
import json
import logging

from almabtrieb.amqp.message_type import message_type_for_routing_key
from almabtrieb.base import BaseConnection, MessageType, ReceivedMessage
from almabtrieb.util import censor_password

logger = logging.getLogger(__name__)


try:
    import aio_pika

    class AmqpConnection(BaseConnection):  # type: ignore
        def __init__(
            self,
            connection_string: str,
            username: str,
            echo: bool = False,
            silent: bool = False,
            timeout: int | None = 10,
        ):
            super().__init__(echo=echo, silent=silent)

            self.connection_string = connection_string
            self.channel = None
            self.username = username
            self.timeout = timeout

        @property
        def connected(self):
            return self.channel is not None

        @property
        def subscription_topic(self):
            return f"receive.{self.username}.#"

        @property
        def subscription_topic_error(self):
            return f"error.{self.username}"

        def routing_key(self, topic_end: str):
            """
            ```pycon
            >>> connection = AmqpConnection("amqp://guest:guest@localhost/", "alice")
            >>> connection.routing_key("example.one")
            'send.alice.example.one'

            >>> connection.routing_key("example/two")
            'send.alice.example.two'

            ```
            """

            return f"send.{self.username}.{topic_end.replace('/', '.')}"

        async def run(self):
            try:
                if not self.silent:
                    logger.info(
                        "Conneting to amqp with %s",
                        censor_password(self.connection_string),
                    )
                connection = await aio_pika.connect_robust(
                    self.connection_string, timeout=self.timeout
                )

                async with connection:
                    self.channel = await connection.channel()

                    await self.channel.set_qos(prefetch_count=1)
                    self.exchange = await self.channel.declare_exchange(
                        "amq.topic",
                        aio_pika.ExchangeType.TOPIC,
                        durable=True,
                    )

                    queue = await self.channel.declare_queue(
                        "almabtrieb_queue_" + str(uuid4()),
                        durable=False,
                        auto_delete=True,
                    )

                    await queue.bind(self.exchange, routing_key=self.subscription_topic)
                    await queue.bind(
                        self.exchange, routing_key=self.subscription_topic_error
                    )

                    async with queue.iterator() as iterator:
                        async for message in iterator:
                            async with message.process():
                                await self.handle_message(message)
            except Exception as e:
                await self.handle_termination()
                logger.exception(e)

        async def handle_message(self, message: aio_pika.abc.AbstractIncomingMessage):
            routing_key = message.routing_key

            if routing_key is None:
                logger.exception("Received message without routing key")
                return

            message_type = message_type_for_routing_key(routing_key)

            if message_type == MessageType.deprecated:
                return

            await self.handle(
                ReceivedMessage(
                    message_type=message_type,
                    correlation_id=message.correlation_id,
                    data=json.loads(message.body),
                ),
            )

        async def send(
            self,
            topic_end: str,
            data: dict[str, Any],
            correlation_data: str | None = None,
        ) -> str:
            if correlation_data is None:
                correlation_data = str(uuid4())
            await self.exchange.publish(
                aio_pika.Message(
                    body=json.dumps(data).encode(),
                    correlation_id=correlation_data,
                ),
                routing_key=self.routing_key(topic_end),
            )

            if self.echo:
                logger.info(
                    "Sent %s %s",
                    self.routing_key(topic_end),
                    json.dumps(data, indent=2),
                )

            return correlation_data

except ImportError:

    class AmqpConnection:
        def __init__(self, *args, **kwargs):
            raise ImportError("aio_pika is not installed")
