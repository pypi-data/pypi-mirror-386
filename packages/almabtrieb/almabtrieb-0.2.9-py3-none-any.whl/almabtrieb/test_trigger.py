from unittest.mock import AsyncMock

import pytest

from almabtrieb.base import BaseConnection
from almabtrieb.exceptions import UnsupportedMethodException

from .model import InformationResponse, MethodInformationModel, NameAndVersion
from almabtrieb import Almabtrieb


@pytest.fixture
def information_response():
    name_and_version = NameAndVersion(name="name", version="0.1.2")
    return InformationResponse(
        accountName="test",
        actors=[],
        baseUrls=[],
        methodInformation=[],
        backend=name_and_version,
        protocol=name_and_version,
    )


async def test_trigger_unknown(information_response: InformationResponse):
    almabtrieb = Almabtrieb(connection=AsyncMock(connected=True))
    almabtrieb.information = information_response

    with pytest.raises(UnsupportedMethodException):
        await almabtrieb.trigger("unknown", {})


async def test_trigger_known(information_response: InformationResponse):
    almabtrieb = Almabtrieb(connection=AsyncMock(BaseConnection, connected=True))
    information_response.method_information.append(
        MethodInformationModel(routing_key="known", module="my_module")
    )

    almabtrieb.information = information_response

    await almabtrieb.trigger("known", {})

    almabtrieb.connection.send.assert_awaited_once()  # type: ignore
    almabtrieb.connection.send_with_reply.assert_not_awaited()  # type: ignore


async def test_trigger_known_replies(information_response: InformationResponse):
    almabtrieb = Almabtrieb(connection=AsyncMock(BaseConnection, connected=True))
    information_response.method_information.append(
        MethodInformationModel(routing_key="known", module="my_module", replies=True)
    )

    almabtrieb.information = information_response

    await almabtrieb.trigger("known", {})

    almabtrieb.connection.send.assert_not_awaited()  # type: ignore
    almabtrieb.connection.send_with_reply.assert_awaited_once()  # type: ignore
