import asyncio
import logging

from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import Any
from collections.abc import AsyncGenerator, Awaitable, Callable
import warnings

from almabtrieb.stream import Stream

from .amqp import AmqpConnection
from .mqtt import MqttConnection
from .model import (
    InformationResponse,
    CreateActorRequest,
    FetchMessage,
    FetchResponse,
    MethodInformationModel,
)
from .exceptions import (
    NoIncomingException,
    ErrorMessageException,
    UnsupportedMethodException,
)
from .util import ConnectionParams

__all__ = [
    "Almabtrieb",
    "NoIncomingException",
    "UnsupportedMethodException",
    "ErrorMessageException",
]

logger = logging.getLogger(__name__)


@dataclass
class Almabtrieb:
    """Implements the asynchronous API of the Cattle Drive Protocol"""

    connection: MqttConnection | AmqpConnection
    information: InformationResponse | None = None

    @property
    def connected(self):
        """Is one connected to the service"""
        return self.connection.connected

    def allowed_methods(self) -> list[str]:
        """Returns the set of methods allowed by the connection"""
        if not self.connected:
            raise Exception("information property not set")

        if not self.information:
            raise Exception("information property not set")

        return [method.routing_key for method in self.information.method_information]

    def method_information_for_routing_key(
        self, routing_key: str
    ) -> MethodInformationModel | None:
        if not self.information:
            raise Exception("information property not set")

        for method in self.information.method_information:
            if method.routing_key == routing_key:
                return method
        return None

    @staticmethod
    def from_connection_string(
        connection_string: str, echo: bool = False, silent: bool = False
    ):
        """Creates instance for connection string

        ```python
        Almabtrieb.from_connection_string("ws://user:pass@host/ws")
        Almabtrieb.from_connection_string("amqp://user:pass@host/ws")
        ```

        :param connection_string: The connection string
        :param echo: Set to true to log all messages
        """

        params = ConnectionParams.from_string(connection_string)

        if params.protocol in ["ws", "wss", "mqtt"]:
            return Almabtrieb(
                connection=MqttConnection.from_connection_string(
                    connection_string, echo=echo, silent=silent
                )
            )
        elif params.protocol == "amqp":
            if params.username is None:
                raise ValueError("Username is required for connection")
            return Almabtrieb(
                connection=AmqpConnection(
                    connection_string=connection_string,
                    echo=echo,
                    username=params.username,
                    silent=silent,
                )
            )
        else:
            raise NotImplementedError("Protocol not implemented")

    def add_on_disconnect(self, on_disconnect: Callable[[], Awaitable[None]]):
        """Adds the on disconnect handler"""
        if not self.connection:
            raise ValueError("Connection not set")

        self.connection.on_disconnect.append(on_disconnect)

    async def run(self):
        """Starts the connection and queries for new received messages

        ```python
        task = asyncio.create_task(almabtrieb.run())
        ...
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        ```
        """
        try:
            await self.connection.run()
            logger.info("Run terminated")
        except Exception as e:
            logger.info("Ran into exception when running connection")
            logger.exception(e)

    async def info(self) -> InformationResponse:
        """Returns the information about the connected
        Cattle Drive server. The response is stored
        in  the `information` property.

        :returns: The information about the server
        """
        result = await self.connection.send_with_reply("request/info", {})

        self.information = InformationResponse.model_validate(result)
        return self.information

    async def create_actor(
        self,
        base_url: str,
        preferred_username: str | None = None,
        profile: dict[str, Any] = {},
        automatically_accept_followers: bool | None = None,
        name: str | None = None,
    ) -> dict[str, Any]:
        """Creates a new actor

        :param base_url: The base url of the actor
        :param preferred_username: The preferred username used as `acct:preferred_username@domain` where `domain` is from `base_url`
        :param profile: The profile of the actor
        :param automatically_accept_followers: If true, the server will automatically accept followers
        :param name: The internal name of the actor
        :returns: The created actor profile
        """
        request = CreateActorRequest(
            base_url=base_url,
            preferred_username=preferred_username,
            profile=profile,
            automatically_accept_followers=automatically_accept_followers,
            name=name,
        )

        return await self.connection.send_with_reply(
            "request/create_actor", request.model_dump()
        )

    async def fetch(self, actor: str, uri: str, timeout: float = 1) -> FetchResponse:
        """Fetches the object with uri `uri` as the actor with actor id `actor`.

        :param actor: The actor id must be part of actors from the info response
        :param uri: The uri of the object to fetch
        :param timeout: The timeout for the request
        :returns: The fetched object
        """
        async with asyncio.timeout(timeout):
            result = await self.connection.send_with_reply(
                "request/fetch", FetchMessage(actor=actor, uri=uri).model_dump()
            )

            return FetchResponse.model_validate(result)

    async def trigger(self, method: str, data: dict[str, Any]):
        """Triggers a method on the backend. Checks that method
        is contained in the methods from the information response.
        Allowed methods correspond to the routing_key property
        of the method_property in [InformationResponse][almabtrieb.model.InformationResponse].

        If the information property is not set, an info call is done. If the information
        contains the `replies` flag, a reply is awaited and returned."""
        end = f"trigger/{method}"

        if not self.information:
            await self.info()

        method_info = self.method_information_for_routing_key(method)

        if not method_info:
            raise UnsupportedMethodException(
                f"Method {method} is not supported by the backend"
            )

        if method_info.replies:
            return await self.connection.send_with_reply(
                end,
                data,
            )

        return await self.connection.send(
            end,
            data,
        )

    def incoming(self) -> Stream[dict[str, Any]]:
        """Generator for the incoming messages"""
        return Stream(self.connection.incoming_queue)

    def outgoing(self) -> Stream[dict[str, Any]]:
        """Generator for the outgoing messages"""
        return Stream(self.connection.outgoing_queue)

    def error(self) -> Stream[dict[str, Any]]:
        """Generator for the outgoing messages"""
        return Stream(self.connection.error_queue)

    async def next_incoming(self, timeout: float = 1) -> dict[str, Any]:
        """Returns the next incoming message

        !!! warning
            deprectated use self.incoming().next()

        :param timeout: The timeout for the request
        :returns: The next incoming message
        """
        warnings.warn(
            "Use self.incoming().next() instead", DeprecationWarning, stacklevel=2
        )

        return await self.incoming().next(timeout=timeout)  # type: ignore

    async def next_outgoing(self, timeout: float = 1) -> dict:
        """Returns the next outgoing message

        !!! warning
            deprectated use self.outgoing().next()

        :param timeout: The timeout for the request
        :returns: The next outgoing message
        """
        warnings.warn(
            "Use self.outgoing().next() instead", DeprecationWarning, stacklevel=2
        )

        return await self.outgoing().next(timeout=timeout)  # type: ignore

    async def next_error(self, timeout: float = 1) -> dict:
        """Returns the next error message

        !!! warning
            deprectated use self.error().next()

        :param timeout: The timeout for the request
        :returns: The next error message
        """
        warnings.warn(
            "Use self.error().next() instead", DeprecationWarning, stacklevel=2
        )

        return await self.error().next(timeout=timeout)  # type: ignore

    async def clear_incoming(self) -> None:
        """Empties the incoming message queue



        !!! warning
            deprectated use self.incoming().clear()

        """
        warnings.warn(
            "Use self.incoming().clear() instead", DeprecationWarning, stacklevel=2
        )
        await self.incoming().clear()

    async def __aenter__(self):
        self.task = asyncio.create_task(self.run())
        while not self.connected:
            if self.task.done():
                raise ConnectionError("Could not connect to server")
            logger.info("Waiting for connection")
            await asyncio.sleep(0.5)

        await self.info()

    async def __aexit__(self, exc_type, exc, tb):
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass


@asynccontextmanager
async def connect(
    connection_string: str, echo: bool = False, sleep_time: float = 0.5
) -> AsyncGenerator[Almabtrieb, None]:
    """Connects to the service

    Usage
    ```python
    async with connect("ws://user:pass@host/ws") as almabtrieb:
        print(await almabtrieb.info())
    ```

    :param connection_string: The connection string
    :param echo: Set to true to log all messages
    :param sleep_time: The time to wait between checking if connected
    """
    almabtrieb = Almabtrieb.from_connection_string(
        connection_string=connection_string,
        echo=echo,
    )

    task = asyncio.create_task(almabtrieb.run())
    while not almabtrieb.connected:
        if task.done():
            raise ConnectionError("Could not connect to server")
        logger.info("Waiting for connection")
        await asyncio.sleep(sleep_time)
    try:
        await almabtrieb.info()
        yield almabtrieb
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
