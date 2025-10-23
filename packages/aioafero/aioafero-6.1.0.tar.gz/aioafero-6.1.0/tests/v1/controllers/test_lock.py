"""Test LockController"""

import pytest

from aioafero.device import AferoState
from aioafero.v1.controllers import event
from aioafero.v1.controllers.lock import LockController, features

from .. import utils

lock = utils.create_devices_from_data("door-lock-TBD.json")[0]


@pytest.fixture
def mocked_controller(mocked_bridge, mocker):
    mocker.patch("time.time", return_value=12345)
    return mocked_bridge.locks


@pytest.mark.asyncio
async def test_initialize(mocked_controller):
    await mocked_controller.initialize_elem(lock)
    assert len(mocked_controller.items) == 1
    dev = mocked_controller.items[0]
    assert dev.id == "698e8a63-e8cb-4335-ba6b-83ca69d378f2"
    assert dev.position == features.CurrentPositionFeature(
        position=features.CurrentPositionEnum.LOCKED
    )


@pytest.mark.asyncio
async def test_lock(mocked_controller):
    await mocked_controller._bridge.events.generate_events_from_data(
        [utils.create_hs_raw_from_device(lock)]
    )
    await mocked_controller._bridge.async_block_until_done()
    assert len(mocked_controller.items) == 1
    await mocked_controller.lock(lock.id)
    await mocked_controller._bridge.async_block_until_done()
    assert mocked_controller.items[0].position.position == features.CurrentPositionEnum.LOCKING


@pytest.mark.asyncio
async def test_unlock(mocked_controller):
    await mocked_controller._bridge.events.generate_events_from_data(
        [utils.create_hs_raw_from_device(lock)]
    )
    await mocked_controller._bridge.async_block_until_done()
    assert len(mocked_controller.items) == 1
    await mocked_controller.unlock(lock.id)
    await mocked_controller._bridge.async_block_until_done()
    assert mocked_controller.items[0].position.position == features.CurrentPositionEnum.UNLOCKING


@pytest.mark.asyncio
async def test_empty_update(mocked_controller):
    await mocked_controller._bridge.events.generate_events_from_data(
        [utils.create_hs_raw_from_device(lock)]
    )
    await mocked_controller._bridge.async_block_until_done()
    assert len(mocked_controller.items) == 1
    update = utils.create_devices_from_data("door-lock-TBD.json")[0]
    updates = await mocked_controller.update_elem(update)
    assert updates == set()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "value, expected, expected_updates",
    [
        ("locking", features.CurrentPositionEnum.LOCKING, {"position"}),
        ("unlocking", features.CurrentPositionEnum.UNLOCKING, {"position"}),
        ("not-a-state", features.CurrentPositionEnum.UNKNOWN, {"position"}),
    ],
)
async def test_update_elem(value, expected, expected_updates, mocked_controller):
    await mocked_controller._bridge.events.generate_events_from_data(
        [utils.create_hs_raw_from_device(lock)]
    )
    await mocked_controller._bridge.async_block_until_done()
    assert len(mocked_controller.items) == 1
    dev = mocked_controller.items[0]
    assert dev.available
    dev_update = utils.create_devices_from_data("door-lock-TBD.json")[0]
    new_states = [
        AferoState(
            functionClass="lock-control", value=value, lastUpdateTime=0, functionInstance=None
        ),
        AferoState(
            functionClass="available", value=False, lastUpdateTime=0, functionInstance=None
        ),
    ]
    expected_updates.add("available")
    for state in new_states:
        utils.modify_state(dev_update, state)
    updates = await mocked_controller.update_elem(dev_update)
    assert dev.position.position == expected
    assert not dev.available
    assert updates == expected_updates


@pytest.mark.asyncio
async def test_set_state_empty(mocked_controller):
    await mocked_controller._bridge.events.generate_events_from_data(
        [utils.create_hs_raw_from_device(lock)]
    )
    await mocked_controller._bridge.async_block_until_done()
    await mocked_controller.set_state(lock.id)


@pytest.mark.asyncio
async def test_lock_emitting(bridge):
    dev_update = utils.create_devices_from_data("door-lock-TBD.json")[0]
    add_event = {
        "type": "add",
        "device_id": dev_update.id,
        "device": dev_update,
    }
    # Simulate a poll
    bridge.events.emit(event.EventType.RESOURCE_ADDED, add_event)
    await bridge.async_block_until_done()
    assert len(bridge.locks._items) == 1
    # Simulate an update
    utils.modify_state(
        dev_update,
        AferoState(
            functionClass="available",
            functionInstance=None,
            value=False,
        ),
    )
    update_event = {
        "type": "update",
        "device_id": dev_update.id,
        "device": dev_update,
    }
    bridge.events.emit(event.EventType.RESOURCE_UPDATED, update_event)
    await bridge.async_block_until_done()
    assert len(bridge.locks._items) == 1
    assert not bridge.locks._items[dev_update.id].available
