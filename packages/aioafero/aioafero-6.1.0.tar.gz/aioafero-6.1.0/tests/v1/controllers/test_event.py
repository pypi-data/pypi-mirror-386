import asyncio
import copy
import logging
from unittest.mock import AsyncMock

from aioafero.v1.v1_const import VERSION_POLL_INTERVAL_SECONDS
from aiohttp.web_exceptions import HTTPForbidden, HTTPTooManyRequests
import pytest
from datetime import datetime, timedelta, timezone

from aioafero import InvalidAuth
from aioafero.v1.controllers import (
    event,
    exhaust_fan,
    light,
    portable_ac,
    security_system,
)
from aioafero.v1.models.resource import ResourceTypes

from .. import utils

a21_light = utils.create_devices_from_data("light-a21.json")[0]
switch = utils.create_devices_from_data("switch-HPDA311CWB.json")[0]


@pytest.mark.asyncio
async def test_properties(bridge):
    stream = bridge.events
    assert len(stream._scheduled_tasks) == 2
    stream._status = event.EventStreamStatus.CONNECTING
    assert stream.connected is False
    assert stream.status == event.EventStreamStatus.CONNECTING
    stream._status = event.EventStreamStatus.CONNECTED
    assert stream.connected is True
    stream.polling_interval = 1
    assert stream._polling_interval == 1
    assert stream.polling_interval == 1
    assert stream.registered_multiple_devices == {
        "exhaust-fan": exhaust_fan.exhaust_fan_callback,
        "light": light.light_callback,
        "portable-air-conditioner": portable_ac.portable_ac_callback,
        "security-system-sensor": security_system.security_system_callback,
    }
    stream._version_poll_time = None
    assert stream.poll_version is True
    assert stream.poll_version is False
    stream._version_poll_time = datetime.now(timezone.utc) - timedelta(seconds=VERSION_POLL_INTERVAL_SECONDS)
    assert stream.poll_version is True
    stream._version_poll_time = datetime.now(timezone.utc) - timedelta(seconds=VERSION_POLL_INTERVAL_SECONDS)
    stream._version_poll_enabled = False
    assert stream.poll_version is False




@pytest.mark.asyncio
async def test_initialize(bridge):
    stream = bridge.events
    assert len(stream._scheduled_tasks) == 2
    await stream.initialize()
    assert len(stream._scheduled_tasks) == 2


@pytest.mark.asyncio
async def test_stop(bridge):
    stream = bridge.events
    await stream.stop()
    assert len(stream._scheduled_tasks) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "call,event_filter,resource_filter,expected",
    [
        (min, None, None, (min, None, None)),
        (
            min,
            event.EventType.RESOURCE_UPDATED,
            max,
            (min, (event.EventType.RESOURCE_UPDATED,), (max,)),
        ),
        (
            min,
            (event.EventType.RESOURCE_UPDATED, event.EventType.RESOURCE_DELETED),
            max,
            (
                min,
                (event.EventType.RESOURCE_UPDATED, event.EventType.RESOURCE_DELETED),
                (max,),
            ),
        ),
    ],
)
async def test_subscribe(call, event_filter, resource_filter, expected, mocked_bridge_req):
    events = mocked_bridge_req.events
    unsub = events.subscribe(call, event_filter, resource_filter)
    assert callable(unsub)
    assert len(events._subscribers) == 1
    assert events._subscribers[0] == expected
    unsub()
    assert len(events._subscribers) == 0


@pytest.mark.asyncio
async def test_event_reader_dev_add(bridge, mocker):
    stream = bridge.events
    stream._subscribers = []
    await stream.stop()

    light_raw = utils.get_raw_dump("light-a21-raw.json")

    mocker.patch.object(bridge, "fetch_data", AsyncMock(return_value=light_raw))
    await stream.initialize_reader()
    max_retry = 10
    retry = 0
    while True:
        if retry >= max_retry:
            raise AssertionError("Item never added")
        if stream._event_queue.qsize() == 0:
            retry += 1
            await asyncio.sleep(0.1)
        else:
            break
    await stream._bridge.async_block_until_done()
    assert stream._event_queue.qsize() != 0
    polled_data = await stream._event_queue.get()
    assert polled_data["type"] == event.EventType.POLLED_DATA
    polled_devices = await stream._event_queue.get()
    assert polled_devices["type"] == event.EventType.POLLED_DEVICES
    assert len(polled_devices["polled_devices"]) == 1
    event_to_process = await stream._event_queue.get()
    assert event_to_process == {
        "type": event.EventType.RESOURCE_ADDED,
        "device_id": a21_light.id,
        "device": a21_light,
        "force_forward": False,
    }


@pytest.mark.asyncio
async def test_add_job(bridge, mocker):
    stream = bridge.events
    await stream.stop()
    stream.add_job(None)
    assert stream._event_queue.qsize() == 1


def gather_data_happy_path():
    yield []


def gather_data_timeout_gen():
    yield TimeoutError("blah blah blah")
    yield []


def gather_data_error_gen():
    yield HTTPForbidden()
    yield []


def gather_data_multi_error_gen():
    yield HTTPForbidden()
    yield HTTPTooManyRequests()
    yield []


def gather_data_bad_collection():
    yield TypeError(["bad data"])
    yield []


def gather_data_invalid_auth():
    yield InvalidAuth()
    yield []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, response_gen, expected_messages, expected_error, expected_emits",
    [
        # Successful with no issues
        (
            event.EventStreamStatus.CONNECTING,
            gather_data_happy_path,
            [],
            None,
            [event.EventType.CONNECTED],
        ),
        # Successful but already connected
        (
            event.EventStreamStatus.CONNECTED,
            gather_data_happy_path,
            [],
            None,
            [],
        ),
        # Timeout error
        (
            event.EventStreamStatus.CONNECTING,
            gather_data_timeout_gen,
            ["Timeout when contacting Afero IoT API"],
            None,
            [event.EventType.DISCONNECTED, event.EventType.CONNECTED],
        ),
        # Unknown error
        (event.EventStreamStatus.CONNECTING, None, ["kaboom"], KeyError("kaboom"), []),
        # Retry error
        (
            event.EventStreamStatus.CONNECTING,
            gather_data_error_gen,
            ["seconds before next poll", "Lost connection to the Afero IoT API"],
            None,
            [event.EventType.DISCONNECTED, event.EventType.RECONNECTED],
        ),
        # Ensure the messages only appears once
        (
            event.EventStreamStatus.CONNECTING,
            gather_data_multi_error_gen,
            ["Lost connection to the Afero IoT API"],
            None,
            [event.EventType.DISCONNECTED, event.EventType.RECONNECTED],
        ),
        # Data comes back incorrectly from Hubspace
        (
            event.EventStreamStatus.CONNECTING,
            gather_data_bad_collection,
            ["Unexpected data from Afero IoT API, ['bad data']"],
            None,
            [event.EventType.DISCONNECTED, event.EventType.RECONNECTED],
        ),
        # Invalid refresh token
        (
            event.EventStreamStatus.CONNECTING,
            gather_data_invalid_auth,
            ["Invalid credentials provided."],
            None,
            [event.EventType.DISCONNECTED, event.EventType.RECONNECTED],
        ),
    ],
)
async def test_gather_data(
    status,
    response_gen,
    expected_messages,
    expected_error,
    expected_emits,
    bridge,
    mocker,
    caplog,
):
    caplog.set_level(logging.DEBUG)
    stream = bridge.events
    stream.polling_interval = 0.0
    await stream.stop()
    stream._status = status

    if response_gen:
        mocker.patch.object(
            bridge,
            "fetch_data",
            side_effect=response_gen(),
        )
    else:
        mocker.patch.object(
            bridge,
            "fetch_data",
            side_effect=expected_error,
        )
    emit_calls = mocker.patch.object(stream, "emit")
    if response_gen:
        await stream.gather_data()
    else:
        with pytest.raises(expected_error.__class__):
            await stream.gather_data()
    assert emit_calls.call_count == len(expected_emits)
    for index, emit in enumerate(expected_emits):
        assert emit_calls.call_args_list[index][0][0] == emit, f"Issue at index {index}"
    for message in expected_messages:
        assert message in caplog.text
        assert caplog.text.count(message) == 1


@pytest.mark.asyncio
async def test_generate_events_from_data(bridge, mocker):
    stream = bridge.events
    await stream.stop()
    raw_data = []
    raw_data.extend(utils.create_hs_raw_from_dump("light-a21.json"))
    raw_data.append(utils.create_hs_raw_from_dump("switch-HPDA311CWB.json")[0])
    bridge._known_devs = {
        switch.id: bridge.switches,
        "doesnt_exist_list": bridge.lights,
    }
    bad_device = utils.create_hs_raw_from_dump("switch-HPDA311CWB.json")[0]
    bad_device["description"]["device"]["deviceClass"] = ""
    raw_data.append(bad_device)
    # Show what happens when no multi-devs are found
    stream.register_multi_device("security-system-sensor", security_system_callback)
    await stream.generate_events_from_data(raw_data)
    await stream._bridge.async_block_until_done()
    assert stream._event_queue.qsize() == 5
    polled_data = await stream._event_queue.get()
    assert polled_data["type"] == event.EventType.POLLED_DATA
    polled_devices = await stream._event_queue.get()
    assert polled_devices["type"] == event.EventType.POLLED_DEVICES
    assert len(polled_devices["polled_devices"]) == 2
    assert await stream._event_queue.get() == {
        "type": event.EventType.RESOURCE_ADDED,
        "device_id": a21_light.id,
        "device": a21_light,
        "force_forward": False,
    }
    assert await stream._event_queue.get() == {
        "type": event.EventType.RESOURCE_UPDATED,
        "device_id": switch.id,
        "device": switch,
        "force_forward": False,
    }
    assert await stream._event_queue.get() == {
        "type": event.EventType.RESOURCE_DELETED,
        "device_id": "doesnt_exist_list",
    }


def get_sensor_ids(device) -> set[int]:
    """Determine available sensors from the states"""
    sensor_ids = set()
    for state in device.states:
        if state.functionInstance is None:
            continue
        if state.functionInstance.startswith("sensor-") and state.value is not None:
            sensor_id = int(state.functionInstance.split("-", 1)[1])
            sensor_ids.add(sensor_id)
    return sensor_ids


def generate_sensor_name(afero_device, sensor_id: int) -> str:
    return f"{afero_device.id}-sensor-{sensor_id}"


def get_valid_states(afero_states: list, sensor_id: int) -> list:
    valid_states: list = []
    for state in afero_states:
        if (
            state.functionClass not in ["sensor-state", "sensor-config"]
            or state.value is None
        ):
            continue
        state_sensor_split = state.functionInstance.rsplit("-", 1)
        state_sensor_id = int(state_sensor_split[1])
        if state_sensor_id != sensor_id:
            continue
        valid_states.append(state)
    return valid_states


def security_system_callback(afero_device) -> event.CallbackResponse:
    multi_devs = []
    if afero_device.device_class == "security-system":
        for sensor_id in get_sensor_ids(afero_device):
            cloned = copy.deepcopy(afero_device)
            cloned.device_id = generate_sensor_name(afero_device, sensor_id)
            cloned.id = generate_sensor_name(afero_device, sensor_id)
            cloned.device_class = "security-system-sensor"
            cloned.friendly_name = f"{afero_device.friendly_name} - Sensor {sensor_id}"
            cloned.states = get_valid_states(afero_device.states, sensor_id)
            cloned.is_multi = True
            multi_devs.append(cloned)
    return event.CallbackResponse(
        split_devices=multi_devs,
        remove_original=False,
    )


@pytest.mark.asyncio
async def test_generate_events_from_data_multi(bridge):
    stream = bridge.events
    await stream.stop()
    afero_data = utils.get_raw_dump("security-system-raw.json")
    stream.register_multi_device("security-system-sensor", security_system_callback)
    await stream.generate_events_from_data(afero_data)
    assert stream._event_queue.qsize() == 7
    polled_data = await stream._event_queue.get()
    assert polled_data["type"] == event.EventType.POLLED_DATA
    polled_devices = await stream._event_queue.get()
    assert polled_devices["type"] == event.EventType.POLLED_DEVICES
    assert len(polled_devices["polled_devices"]) == 5
    security_keypad_event = await stream._event_queue.get()
    assert security_keypad_event["type"] == event.EventType.RESOURCE_ADDED
    assert security_keypad_event["device_id"] == "1f31be19-b9b9-4ca8-8a22-20d0015ec2dd"
    security_system_event = await stream._event_queue.get()
    assert security_system_event["type"] == event.EventType.RESOURCE_ADDED
    assert security_system_event["device_id"] == "7f4e4c01-e799-45c5-9b1a-385433a78edc"
    assert security_system_event["device"].children == [
        "7f4e4c01-e799-45c5-9b1a-385433a78edc-sensor-1",
        "7f4e4c01-e799-45c5-9b1a-385433a78edc-sensor-2",
        "7f4e4c01-e799-45c5-9b1a-385433a78edc-sensor-4",
    ]
    sensor_one = await stream._event_queue.get()
    assert sensor_one["type"] == event.EventType.RESOURCE_ADDED
    assert sensor_one["device_id"] == "7f4e4c01-e799-45c5-9b1a-385433a78edc-sensor-1"
    assert len(sensor_one["device"].states) == 2
    sensor_two = await stream._event_queue.get()
    assert sensor_two["type"] == event.EventType.RESOURCE_ADDED
    assert sensor_two["device_id"] == "7f4e4c01-e799-45c5-9b1a-385433a78edc-sensor-2"
    assert len(sensor_two["device"].states) == 2
    sensor_four = await stream._event_queue.get()
    assert sensor_four["type"] == event.EventType.RESOURCE_ADDED
    assert sensor_four["device_id"] == "7f4e4c01-e799-45c5-9b1a-385433a78edc-sensor-4"
    assert len(sensor_four["device"].states) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "gather_data_return,gather_data_side_effect,"
        "generate_events_from_data_side_effect,expected_emits,expected_queue"
    ),
    [
        # Happy path
        (
            utils.get_raw_dump("test_event_polled.json"),
            None,
            None,
            [],
            [
                {
                    "type": event.EventType.POLLED_DATA,
                    "polled_data": None,
                    "force_forward": False,
                },
                {
                    "type": event.EventType.POLLED_DEVICES,
                    "polled_devices": None,
                    "force_forward": False,
                },
                {
                    "type": event.EventType.RESOURCE_ADDED,
                    "device_id": a21_light.id,
                    "device": a21_light,
                    "force_forward": False,
                },
                {
                    "type": event.EventType.RESOURCE_UPDATED,
                    "device_id": switch.id,
                    "device": switch,
                    "force_forward": False,
                },
                {
                    "type": event.EventType.RESOURCE_DELETED,
                    "device_id": "doesnt_exist_list",
                },
            ],
        ),
        # Issue collecting data
        (None, KeyError, None, [event.EventType.DISCONNECTED], []),
        # Issue processing collected data
        (None, None, KeyError, [], []),
    ],
)
async def test_perform_poll(
    gather_data_return,
    gather_data_side_effect,
    generate_events_from_data_side_effect,
    expected_emits,
    expected_queue,
    bridge,
    mocker,
):
    stream = bridge.events
    await stream.stop()
    if gather_data_side_effect:
        mocker.patch.object(stream, "gather_data", side_effect=gather_data_side_effect)
    else:
        mocker.patch.object(
            stream, "gather_data", AsyncMock(return_value=gather_data_return)
        )
    if generate_events_from_data_side_effect:
        mocker.patch.object(
            stream,
            "generate_events_from_data",
            side_effect=generate_events_from_data_side_effect,
        )

    bridge._known_devs = {
        switch.id: bridge.switches,
        "doesnt_exist_list": bridge.lights,
    }
    emit_calls = mocker.patch.object(stream, "emit")
    await stream.perform_poll()
    await stream._bridge.async_block_until_done()
    assert emit_calls.call_count == len(expected_emits)
    for index, emit in enumerate(expected_emits):
        assert emit_calls.call_args_list[index][0][0] == emit, f"Issue at index {index}"
    assert stream._event_queue.qsize() == len(expected_queue)
    for index, event_to_process in enumerate(expected_queue):
        if event_to_process["type"] == event.EventType.POLLED_DATA:
            event_to_process["polled_data"] = mocker.ANY
        elif event_to_process["type"] == event.EventType.POLLED_DEVICES:
            event_to_process["polled_devices"] = mocker.ANY
        assert (
            await stream._event_queue.get() == event_to_process
        ), f"Issue at index {index}"


@pytest.mark.asyncio
async def test_event_reader_dev_update(bridge, mocker):
    stream = bridge.events
    bridge.lights.initialize()
    await bridge.lights.initialize_elem(a21_light)
    bridge.add_device(a21_light.id, bridge.lights)
    await stream.stop()

    mocker.patch.object(
        stream,
        "gather_data",
        AsyncMock(return_value=utils.create_hs_raw_from_dump("light-a21.json")),
    )
    await stream.initialize_reader()
    max_retry = 10
    retry = 0
    while True:
        if retry >= max_retry:
            raise AssertionError("Item never added")
        if stream._event_queue.qsize() == 0:
            retry += 1
            await asyncio.sleep(0.1)
        else:
            break
    await stream._bridge.async_block_until_done()
    assert stream._event_queue.qsize() != 0
    polled_data = await stream._event_queue.get()
    assert polled_data["type"] == event.EventType.POLLED_DATA
    polled_devices = await stream._event_queue.get()
    assert polled_devices["type"] == event.EventType.POLLED_DEVICES
    assert len(polled_devices["polled_devices"]) == 1
    event_to_process = await stream._event_queue.get()
    assert event_to_process == {
        "type": event.EventType.RESOURCE_UPDATED,
        "device_id": a21_light.id,
        "device": a21_light,
        "force_forward": False,
    }


@pytest.mark.asyncio
async def test_event_reader_dev_delete(bridge, mocker):
    stream = bridge.events
    bridge.lights.initialize()
    bridge.lights.initialize_elem(a21_light)
    bridge.add_device(a21_light.id, bridge.lights)
    await stream.stop()

    def afero_dev(dev):
        return dev

    mocker.patch.object(bridge, "fetch_data", AsyncMock(return_value=[]))
    mocker.patch.object(event, "get_afero_device", side_effect=afero_dev)
    await stream.initialize_reader()
    max_retry = 10
    retry = 0
    while True:
        if retry >= max_retry:
            raise AssertionError("Item never added")
        if stream._event_queue.qsize() == 0:
            retry += 1
            await asyncio.sleep(0.1)
        else:
            break
    await stream._bridge.async_block_until_done()
    assert stream._event_queue.qsize() != 0
    polled_data = await stream._event_queue.get()
    assert polled_data["type"] == event.EventType.POLLED_DATA
    polled_devices = await stream._event_queue.get()
    assert polled_devices["type"] == event.EventType.POLLED_DEVICES
    event_to_process = await stream._event_queue.get()
    assert event_to_process == {
        "type": event.EventType.RESOURCE_DELETED,
        "device_id": a21_light.id,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pop_event,has_exception",
    [
        (
            {
                "type": event.EventType.RESOURCE_UPDATED,
                "device_id": a21_light.id,
                "device": a21_light,
                "force_forward": False,
            },
            False,
        ),
        (
            {
                "type": event.EventType.RESOURCE_UPDATED,
                "device_id": a21_light.id,
                "device": a21_light,
                "force_forward": False,
            },
            True,
        ),
    ],
)
async def test_process_event(pop_event, has_exception, bridge, mocker, caplog):
    stream = bridge.events
    await stream.stop()
    await stream._event_queue.put(pop_event)
    if not has_exception:
        emit_calls = mocker.patch.object(stream, "emit")
        await stream.process_event()
        assert emit_calls.call_count == 1
    else:
        mocker.patch.object(stream, "emit", side_effect=KeyError)
        await stream.process_event()
        assert "Unhandled exception. Please open a bug report" in caplog.text


@pytest.mark.asyncio
async def test___event_processor(bridge, mocker):
    stream = bridge.events
    emit = mocker.patch.object(stream, "emit")
    exp_event = event.AferoEvent(
        type=event.EventType.RESOURCE_DELETED, device_id="1234"
    )
    stream._event_queue.put_nowait(exp_event)
    await stream.initialize_processor()
    max_retry = 10
    retry = 0
    while True:
        if retry >= max_retry:
            raise AssertionError("Item never removed")
        if stream._event_queue.qsize() == 1:
            retry += 1
            await asyncio.sleep(0.1)
        else:
            break
    assert stream._event_queue.qsize() == 0
    emit.assert_called_once_with(exp_event["type"], exp_event)


@pytest.mark.asyncio
@pytest.mark.parametrize("is_coroutine", [True, False])
@pytest.mark.parametrize(
    "event_type, event_filter, expected",
    [
        (event.EventType.RESOURCE_ADDED, (event.EventType.RESOURCE_ADDED,), True),
        (event.EventType.RESOURCE_UPDATED, (event.EventType.RESOURCE_ADDED,), False),
    ],
)
async def test_emit_event_type(
    event_type, event_filter, expected, is_coroutine, bridge, mocker
):
    stream = bridge.events
    stream._subscribers = []
    await stream.stop()

    event_to_emit = event.AferoEvent(
        type=event_type, device_id=a21_light.id, device=a21_light
    )

    callback = mocker.AsyncMock() if is_coroutine else mocker.Mock()
    stream.subscribe(callback, event_filter=event_filter)
    stream.emit(event_type, event_to_emit)
    if expected:
        callback.assert_called_once()
    else:
        callback.assert_not_called()


@pytest.mark.asyncio
async def test_emit_invalid_auth(bridge, mocker):
    stream = bridge.events
    stream._subscribers = []
    await stream.stop()
    callback = mocker.AsyncMock()
    event_type = event.EventType.INVALID_AUTH
    stream.subscribe(callback, event_filter=(event_type,))
    event_to_emit = event.AferoEvent(type=event_type)
    stream.emit(event_type, event_to_emit)
    callback.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("is_coroutine", [True, False])
@pytest.mark.parametrize(
    "device, resource_filter, expected",
    [
        (a21_light, (ResourceTypes.LIGHT,), True),
        (a21_light, (ResourceTypes.FAN,), False),
        (
            switch,
            (
                ResourceTypes.LIGHT,
                ResourceTypes.FAN,
            ),
            True,
        ),
    ],
)
async def test_emit_resource_filter(
    device, resource_filter, expected, is_coroutine, bridge, mocker
):
    stream = bridge.events
    await stream.stop()

    event_to_emit = event.AferoEvent(
        type=event.EventType.RESOURCE_UPDATED, device_id=device.id, device=device
    )

    callback = mocker.AsyncMock() if is_coroutine else mocker.Mock()
    res_filter = tuple(x.value for x in resource_filter)
    stream.subscribe(callback, resource_filter=res_filter)
    stream.emit(event.EventType.RESOURCE_UPDATED, event_to_emit)
    if expected:
        callback.assert_called_once()
    else:
        callback.assert_not_called()


@pytest.mark.asyncio
async def test_emit_resource_filter_exception(bridge, caplog):
    stream = bridge.events
    event_to_emit = event.AferoEvent(
        type=event.EventType.RESOURCE_UPDATED,
        device_id="cool_id",
        device="im not a hubspace device",
    )
    stream.subscribe(min, resource_filter=(ResourceTypes.LIGHT.value,))
    stream.emit(event.EventType.RESOURCE_UPDATED, event_to_emit)
    assert "Unhandled exception. Please open a bug report" in caplog.text


@pytest.mark.asyncio
async def test_wait_for_first_poll(bridge):
    stream = bridge.events
    await stream.stop()
    assert stream._first_poll_completed is True
    stream._first_poll_completed = False
    task = asyncio.create_task(stream.wait_for_first_poll())
    await asyncio.sleep(0.1)
    assert task.done() is False
    stream._first_poll_completed = True
    await asyncio.sleep(0.1)
    assert task.done() is True
