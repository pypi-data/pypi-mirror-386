import datetime
import asyncio

from aioresponses import aioresponses
import pytest
import pytest_asyncio
import aiohttp

from aioafero.v1 import AferoBridgeV1
from aioafero import AferoDevice
from aioafero.v1.auth import TokenData
from aioafero.v1.controllers.event import EventType
from tests.v1.utils import create_hs_raw_from_device
from aioafero.v1.controllers.base import BaseResourcesController, dataclass_to_afero
import securelogging


@pytest.fixture(autouse=True)
def reset_logging_secrets():
    securelogging._called_from_test = True
    securelogging.reset_secrets()
    yield


@pytest_asyncio.fixture(scope="function")
async def aio_sess() -> aiohttp.ClientSession:
    yield aiohttp.ClientSession()


@pytest_asyncio.fixture
async def mocked_bridge(mocker, aio_sess) -> AferoBridgeV1:
    """Create a mocked afero bridge to be used in tests."""
    mocker.patch("time.time", return_value=12345)
    mocker.patch("aioafero.v1.controllers.event.EventStream.gather_data")

    bridge: AferoBridgeV1 = AferoBridgeV1("username2", "password2")
    mocker.patch.object(bridge, "_account_id", "mocked-account-id")
    mocker.patch.object(bridge, "fetch_data", return_value=[])
    mocker.patch.object(bridge.events, "initialize_reader")
    mocker.patch.object(bridge, "request", side_effect=mocker.AsyncMock())
    mocker.patch.object(
        bridge, "fetch_data", side_effect=mocker.AsyncMock(return_value=[])
    )
    mocker.patch.object(bridge.events, "_first_poll_completed", True)
    mocker.patch.object(bridge, "_web_session", aio_sess)

    bridge.set_token_data(
        TokenData(
            "mock-token",
            "mock-access",
            "mock-refresh-token",
            expiration=datetime.datetime.now().timestamp() + 200,
        )
    )

    # Enable ad-hoc polls
    async def generate_events_from_data(data):
        task = asyncio.create_task(bridge.events.generate_events_from_data(data))
        await task
        raw_data = await bridge.events.generate_events_from_data(data)
        mocker.patch(
            "aioafero.v1.controllers.event.EventStream.gather_data",
            return_value=raw_data,
        )
        await bridge.async_block_until_done()

    # Fake a poll for discovery
    async def generate_devices_from_data(devices: list[AferoDevice]):
        raw_data = [create_hs_raw_from_device(device) for device in devices]
        mocker.patch(
            "aioafero.v1.controllers.event.EventStream.gather_data",
            return_value=raw_data,
        )
        await bridge.events.generate_events_from_data(raw_data)
        await bridge.async_block_until_done()

    # Fake the response from the API when updating states
    def mock_update_afero_api(device_id, result):
        json_resp = mocker.AsyncMock()
        json_resp.return_value = {"metadeviceId": device_id, "values": result}
        resp = mocker.AsyncMock()
        resp.json = json_resp
        resp.status = 200
        mocker.patch("aioafero.v1.controllers.base.BaseResourcesController.update_afero_api", return_value=resp)
    
    # Enable "results" to be returned on update
    actual_dataclass_to_afero = dataclass_to_afero
    def mocked_dataclass_to_afero(*args, **kwargs):
        result = actual_dataclass_to_afero(*args, **kwargs)
        mock_update_afero_api(args[0].id, result)
        return result
    
    mocker.patch("aioafero.v1.controllers.base.dataclass_to_afero", side_effect=mocked_dataclass_to_afero)
    
    bridge.mock_update_afero_api = mock_update_afero_api
    bridge.generate_devices_from_data = generate_devices_from_data
    bridge.generate_events_from_data = generate_events_from_data

    await bridge.initialize()
    yield bridge
    await bridge.close()


@pytest.fixture
def mocked_bridge_req(mocker, aio_sess):
    bridge: AferoBridgeV1 = AferoBridgeV1("username2", "password2")
    mocker.patch.object(
        bridge,
        "get_account_id",
        side_effect=mocker.AsyncMock(return_value="mocked-account-id"),
    )
    mocker.patch.object(bridge, "_account_id", "mocked-account-id")
    mocker.patch.object(bridge, "initialize", side_effect=mocker.AsyncMock())
    mocker.patch.object(bridge, "fetch_data", side_effect=bridge.fetch_data)
    mocker.patch.object(bridge, "request", side_effect=bridge.request)
    mocker.patch.object(bridge, "_web_session", aio_sess)
    mocker.patch.object(bridge.events, "_first_poll_completed", True)
    bridge._auth._token_data = TokenData(
        "mock-token",
        None,
        "mock-refresh-token",
        expiration=datetime.datetime.now().timestamp() + 200,
    )
    # Force initialization so test elements are not overwritten
    for controller in bridge._controllers.values():
        controller._initialized = True

    # Enable ad-hoc event updates
    def emit_event(event_type, data):
        bridge.events.emit(EventType(event_type), data)

    # Enable ad-hoc polls
    async def generate_events_from_data(data):
        task = asyncio.create_task(bridge.events.generate_events_from_data(data))
        await task
        raw_data = await bridge.events.generate_events_from_data(data)
        mocker.patch(
            "aioafero.v1.controllers.event.EventStream.gather_data",
            return_value=raw_data,
        )
        await bridge.async_block_until_done()

    # Fake a poll for discovery
    async def generate_devices_from_data(devices: list[AferoDevice]):
        raw_data = [create_hs_raw_from_device(device) for device in devices]
        mocker.patch(
            "aioafero.v1.controllers.event.EventStream.gather_data",
            return_value=raw_data,
        )
        await bridge.events.generate_events_from_data(raw_data)
        await bridge.async_block_until_done()

    bridge.emit_event = emit_event
    bridge.generate_devices_from_data = generate_devices_from_data
    bridge.generate_events_from_data = generate_events_from_data

    bridge.__aenter__ = mocker.AsyncMock(return_value=bridge)
    bridge.__aexit__ = mocker.AsyncMock()
    return bridge


@pytest_asyncio.fixture
async def bridge(mocker):
    bridge = AferoBridgeV1("user", "passwd")
    mocker.patch.object(bridge, "_account_id", "mocked-account-id")
    mocker.patch.object(bridge, "fetch_data", return_value=[])
    mocker.patch.object(bridge, "request", side_effect=mocker.AsyncMock())
    mocker.patch.object(bridge.events, "_first_poll_completed", True)
    await bridge.initialize()
    await bridge.async_block_until_done()
    yield bridge
    await bridge.close()


@pytest_asyncio.fixture
async def bridge_with_acct(mocker):
    bridge = AferoBridgeV1("user", "passwd")
    bridge._auth._token_data = TokenData(
            "mock-token",
            None,
            "mock-refresh-token",
            expiration=datetime.datetime.now().timestamp() + 200,
        )
    yield bridge


@pytest_asyncio.fixture
async def bridge_with_acct_req(mocker):
    bridge = AferoBridgeV1("user", "passwd")
    mocker.patch.object(bridge, "_account_id", "mocked-account-id")
    mocker.patch.object(bridge, "request", side_effect=bridge.request)
    mocker.patch.object(bridge.events, "_first_poll_completed", True)
    bridge._auth._token_data = TokenData(
            "mock-token",
            None,
            "mock-refresh-token",
            expiration=datetime.datetime.now().timestamp() + 200,
        )
    await bridge.initialize()
    await bridge.async_block_until_done()
    yield bridge
    await bridge.close()


@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m
