from dataclasses import dataclass, field, fields, replace
import logging

import pytest
import asyncio
from aioafero import AferoDevice, AferoState, TemperatureUnit
from aioafero.device import get_afero_device
from aioafero.errors import DeviceNotFound, ExceededMaximumRetries
from aioafero.v1 import AferoBridgeV1, models, v1_const
from aioafero.v1.controllers import event
from aioafero.v1.controllers.base import (
    ID_FILTER_ALL,
    BaseResourcesController,
    NumbersFeature,
    NumbersName,
    dataclass_to_afero,
    get_afero_instance_for_state,
    get_afero_state_from_feature,
    get_afero_states_from_list,
    get_afero_states_from_mapped,
)
from aioafero.v1.models.features import SelectFeature
from aioafero.v1.models.resource import DeviceInformation
import pytest_asyncio

from .. import utils

_LOGGER = logging.getLogger(__name__)



@dataclass
class TestFeatureBool:
    on: bool

    @property
    def api_value(self):
        return self.on


@dataclass
class TestFeatureInstance:
    on: bool
    func_instance: str | None

    @property
    def api_value(self):
        return {
            "value": "on" if self.on else "off",
            "functionClass": "mapped_beans",
            "functionInstance": self.func_instance or "",
        }


@dataclass
class ReturnsAListFeature:
    useless_value: bool

    @property
    def api_value(self):
        return [
            {
                "value": "cool",
                "functionClass": "bean-type",
                "functionInstance": "temperature",
            },
            {
                "value": "bean",
                "functionClass": "bean-type",
                "functionInstance": "warmth",
            },
        ]


@dataclass
class TestResource:
    id: str
    available: bool
    on: TestFeatureBool
    beans: dict[str | None, TestFeatureInstance]
    device_information: DeviceInformation = field(default_factory=DeviceInformation)
    instances: dict = field(default_factory=lambda: dict(), repr=False, init=False)


@dataclass
class TestResourceWithFunctions:
    id: str
    available: bool
    on: TestFeatureBool
    beans: dict[str | None, TestFeatureInstance]
    device_information: DeviceInformation = field(default_factory=DeviceInformation)
    instances: dict = field(default_factory=lambda: dict(), repr=False, init=False)

    def __init__(self, functions: list, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        instances = {}
        for function in functions:
            instances[function["functionClass"]] = function.get(
                "functionInstance", None
            )
        self.instances = instances

    def get_instance(self, elem):
        """Lookup the instance associated with the elem"""
        return self.instances.get(elem, None)


test_res_funcs = TestResourceWithFunctions(
    [{"functionClass": "on", "functionInstance": "super-beans"}],
    id="cool",
    available=True,
    on=TestFeatureBool(on=True),
    beans={
        None: TestFeatureInstance(on=True, func_instance=None),
        "bean1": TestFeatureInstance(on=True, func_instance="bean1"),
        "bean2": TestFeatureInstance(on=False, func_instance="bean2"),
    },
    device_information=DeviceInformation(),
)


@dataclass
class TestResourcePut:
    on: TestFeatureBool | None
    beans: TestFeatureInstance | None


@dataclass
class TestResourcePutCallback:
    on: TestFeatureBool | None
    beans: TestFeatureInstance | None
    callback: callable


@dataclass
class TestResourceList:
    the_beans: ReturnsAListFeature | None


@dataclass
class TestResourceListPut:
    the_beans: ReturnsAListFeature | None = None


@dataclass
class TestResourceDict:
    id: str
    available: bool
    selects: dict[tuple[str, str | None], SelectFeature] | None
    device_information: DeviceInformation = field(default_factory=DeviceInformation)


@dataclass
class TestResourceDictPut:
    selects: dict[tuple[str, str | None], SelectFeature] | None


test_res = TestResource(
    id="cool",
    available=True,
    on=TestFeatureBool(on=True),
    beans={
        None: TestFeatureInstance(on=True, func_instance=None),
        "bean1": TestFeatureInstance(on=True, func_instance="bean1"),
        "bean2": TestFeatureInstance(on=False, func_instance="bean2"),
    },
    device_information=DeviceInformation(
        device_class="light",
    ),
)


test_res_update = TestResource(
    id="cool",
    available=True,
    on=TestFeatureBool(on=True),
    beans={
        None: TestFeatureInstance(on=True, func_instance=None),
        "bean1": TestFeatureInstance(on=True, func_instance="bean1"),
        "bean2": TestFeatureInstance(on=True, func_instance="bean2"),
    },
    device_information=DeviceInformation(
        device_class="light",
    ),
)

test_res_update_multiple = TestResource(
    id="cool",
    available=True,
    on=TestFeatureBool(on=False),
    beans={
        None: TestFeatureInstance(on=True, func_instance=None),
        "bean1": TestFeatureInstance(on=True, func_instance="bean1"),
        "bean2": TestFeatureInstance(on=True, func_instance="bean2"),
    },
    device_information=DeviceInformation(
        device_class="light",
    ),
)


test_res_default_dict = TestResourceDict(
    id="cool",
    available=True,
    selects={
        ("b1", None): SelectFeature(
            selected="True", selects={"True", "False"}, name="b1"
        ),
        ("b2", "one"): SelectFeature(
            selected="beans", selects={"beans", "cool"}, name="b2-1"
        ),
        ("b2", "two"): SelectFeature(
            selected="cool", selects={"beans", "cool"}, name="b2-2"
        ),
    },
    device_information=DeviceInformation(
        device_class="light",
    ),
)


test_res_update_dict = TestResourceDict(
    id="cool",
    available=True,
    selects={
        ("b1", None): SelectFeature(
            selected="False", selects={"True", "False"}, name="b1"
        ),
        ("b2", "one"): SelectFeature(
            selected="cool", selects={"beans", "cool"}, name="b2-1"
        ),
        ("b2", "two"): SelectFeature(
            selected="beans", selects={"beans", "cool"}, name="b2-2"
        ),
    },
    device_information=DeviceInformation(
        device_class="light",
    ),
)

test_device_dict = AferoDevice(
    id="cool",
    device_id="cool-parent",
    model="bean",
    device_class="light",
    default_name="bean",
    default_image="bean",
    friendly_name="bean",
    states=[
        AferoState(
            functionClass="on",
            value="on",
            lastUpdateTime=0,
            functionInstance=None,
        ),
        AferoState(
            functionClass="mapped_beans",
            value="on",
            lastUpdateTime=0,
        ),
        AferoState(
            functionClass="b1",
            value="True",
            lastUpdateTime=0,
            functionInstance=None,
        ),
        AferoState(
            functionClass="b2",
            value="beans",
            lastUpdateTime=0,
            functionInstance="one",
        ),
        AferoState(
            functionClass="b2",
            value="cool",
            lastUpdateTime=0,
            functionInstance="two",
        ),
    ],
    functions=[
        {
            "id": "af2f7826-990d-44bd-a8a1-d890438c7f1a",
            "functionClass": "b1",
            "functionInstance": None,
            "type": "category",
            "values": [
                {
                    "name": "True",
                },
                {
                    "name": "False",
                },
            ],
        },
        {
            "id": "af2f7826-990d-44bd-a8a1-d890438c7f1a",
            "functionClass": "b2",
            "functionInstance": "one",
            "type": "category",
            "values": [
                {
                    "name": "cool",
                },
                {
                    "name": "beans",
                },
            ],
        },
        {
            "id": "af2f7826-990d-44bd-a8a1-d890438c7f1a",
            "functionClass": "b2",
            "functionInstance": "two",
            "type": "category",
            "values": [
                {
                    "name": "cool",
                },
                {
                    "name": "beans",
                },
            ],
        },
    ],
)


test_device = AferoDevice(
    id="cool",
    device_id="cool-parent",
    model="bean",
    device_class="light",
    default_name="bean",
    default_image="bean",
    friendly_name="bean",
    states=[
        AferoState(
            functionClass="power",
            value="on",
            lastUpdateTime=0,
            functionInstance=None,
        ),
        AferoState(
            functionClass="mapped_beans",
            value="on",
            lastUpdateTime=0,
        ),
        AferoState(
            functionClass="mapped_beans",
            value="on",
            lastUpdateTime=0,
            functionInstance="bean1",
        ),
        AferoState(
            functionClass="mapped_beans",
            value="off",
            lastUpdateTime=0,
            functionInstance="bean2",
        ),
    ],
    functions=[],
)

test_device_update = AferoDevice(
    id="cool",
    device_id="cool-parent",
    model="bean",
    device_class="light",
    default_name="bean",
    default_image="bean",
    friendly_name="bean",
    states=[
        AferoState(
            functionClass="power",
            value="on",
            lastUpdateTime=0,
            functionInstance=None,
        ),
        AferoState(
            functionClass="mapped_beans",
            value="on",
            lastUpdateTime=0,
        ),
        AferoState(
            functionClass="mapped_beans",
            value="on",
            lastUpdateTime=0,
            functionInstance="bean1",
        ),
        AferoState(
            functionClass="mapped_beans",
            value="on",
            lastUpdateTime=0,
            functionInstance="bean2",
        ),
    ],
    functions=[],
)


def callback(polled_data: list[dict]):
    return event.CallbackResponse([], False)


class Example1ResourceController(BaseResourcesController):
    ITEM_TYPE_ID: models.ResourceTypes = models.ResourceTypes.DEVICE
    ITEM_TYPES: list[models.ResourceTypes] = [models.ResourceTypes.LIGHT]
    ITEM_CLS = TestResource
    ITEM_MAPPING: dict = {"beans": "mapped_beans"}
    DEVICE_SPLIT_CALLBACKS = {"nada": callback}
    ITEM_NUMBERS: dict[tuple[str, str | None], NumbersName] = {
        ("yup", None): NumbersName(unit="unit", display_name="disp"),
        ("nope", None): NumbersName(unit="unit", display_name=None),
        ("nope", "nope"): NumbersName(unit="unit", display_name=None),
    }

    async def initialize_elem(self, afero_dev: AferoDevice) -> TestResource:
        """Initialize the element"""
        self._logger.info("Initializing %s", afero_dev.id)
        on: TestFeatureBool | None = None
        beans: dict[str | None, TestFeatureInstance] = {}
        for state in afero_dev.states:
            if state.functionClass == "power":
                on = TestFeatureBool(on=state.value == "on")
            elif state.functionClass == "mapped_beans":
                beans[state.functionInstance] = TestFeatureInstance(
                    on=state.value == "on", func_instance=state.functionInstance
                )
        return TestResource(
            id=afero_dev.id,
            available=True,
            on=on,
            beans=beans,
            device_information=DeviceInformation(
                device_class=afero_dev.device_class,
            )
        )

    async def update_elem(self, afero_dev: AferoDevice) -> set:
        updated_keys = set()
        cur_item = self.get_device(afero_dev.id)
        for state in afero_dev.states:
            if state.functionClass == "power":
                new_val = state.value == "on"
                if cur_item.on.on != new_val:
                    updated_keys.add("on")
                    cur_item.on.on = new_val
            elif state.functionClass == "mapped_beans":
                new_val = state.value == "on"
                if cur_item.beans[state.functionInstance].on != new_val:
                    updated_keys.add("on")
                    cur_item.beans[state.functionInstance].on = state.value == "on"
            elif (update_key := await self.update_sensor(state, cur_item)) or (update_key := await self.update_number(state, cur_item)) or (update_key := await self.update_select(state, cur_item)):
                updated_keys.add(update_key)
        return updated_keys


class Example2ResourceController(BaseResourcesController):
    ITEM_TYPE_ID: models.ResourceTypes = models.ResourceTypes.DEVICE
    ITEM_TYPES: list[models.ResourceTypes] = [models.ResourceTypes.LIGHT]
    ITEM_CLS = TestResource
    ITEM_MAPPING: dict = {}
    ITEM_SELECTS = {
        ("b1", None): "b1",
        ("b2", "one"): "b2-1",
        ("b2", "two"): "b2-2",
    }

    async def initialize_elem(self, afero_device: AferoDevice) -> TestResourceDict:
        """Initialize the element"""
        self._logger.info("Initializing %s", afero_device.id)
        selects: dict[tuple[str, str], SelectFeature] = {}
        for state in afero_device.states:
            if select := await self.initialize_select(afero_device.functions, state):
                selects[select[0]] = select[1]
        return TestResourceDict(
            id=afero_device.id,
            available=True,
            selects=selects,
            device_information=DeviceInformation(
                device_class=afero_device.device_class,
            )
        )

    async def update_elem(self, afero_dev: AferoDevice) -> set:
        updated_keys = set()
        cur_item = self.get_device(afero_dev.id)
        for state in afero_dev.states:
            if update_key := await self.update_select(state, cur_item):
                updated_keys.add(update_key)
        return updated_keys


@pytest_asyncio.fixture
async def ex1_rc(bridge_with_acct_req):
    bridge_with_acct_req.add_controller("ex1", Example1ResourceController)
    await bridge_with_acct_req.initialize()
    yield bridge_with_acct_req.ex1


@pytest_asyncio.fixture
async def ex1_rc_mocked(mocked_bridge):
    mocked_bridge.add_controller("ex1", Example1ResourceController)
    await mocked_bridge.initialize()
    yield mocked_bridge.ex1


@pytest_asyncio.fixture
async def ex2_rc(bridge_with_acct_req):
    bridge_with_acct_req.add_controller("ex2", Example2ResourceController)
    await bridge_with_acct_req.initialize()
    yield bridge_with_acct_req.ex2


@pytest_asyncio.fixture
async def ex2_rc_mocked(mocked_bridge):
    mocked_bridge.add_controller("ex2", Example2ResourceController)
    await mocked_bridge.initialize()
    yield mocked_bridge.ex2


def test_init(ex1_rc):
    assert isinstance(ex1_rc._bridge, AferoBridgeV1)
    assert ex1_rc._items == {}
    ex1_rc._initialized = False
    assert not ex1_rc.initialized
    ex1_rc._initialized = True
    assert ex1_rc.initialized
    assert ex1_rc.subscribers == {ID_FILTER_ALL: []}


def test_basic(ex1_rc):
    ex1_rc._items = {"cool": "beans"}
    assert ex1_rc["cool"] == "beans"
    assert "cool" in ex1_rc
    for item in ex1_rc:
        assert item == "beans"
    assert ex1_rc.items == ["beans"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "init_elem, evt_type, item_id, evt_data, expected_devs, expected_return",
    [
        # Device added
        (
            [],
            event.EventType.RESOURCE_ADDED,
            test_device.id,
            event.AferoEvent(
                type=event.EventType.RESOURCE_ADDED,
                device_id=test_device.id,
                device=test_device,
                force_forward=False,
            ),
            {test_device.id},
            replace(test_res),
        ),
        # Device not found
        (
            [],
            event.EventType.RESOURCE_UPDATED,
            test_device.id,
            event.AferoEvent(
                type=event.EventType.RESOURCE_UPDATED,
                device_id=test_device.id,
                device=test_device_update,
                force_forward=False,
            ),
            set(),
            None,
        ),
        # Device updated with changes
        (
            [test_device],
            event.EventType.RESOURCE_UPDATED,
            test_device.id,
            event.AferoEvent(
                type=event.EventType.RESOURCE_UPDATED,
                device_id=test_device.id,
                device=test_device_update,
                force_forward=False,
            ),
            {test_device.id},
            replace(test_res_update),
        ),
        # Device updated with no changes + dont force
        (
            [test_device],
            event.EventType.RESOURCE_UPDATED,
            test_device.id,
            event.AferoEvent(
                type=event.EventType.RESOURCE_UPDATED,
                device_id=test_device.id,
                device=test_device,
                force_forward=False,
            ),
            {test_device.id},
            None,
        ),
        # Device updated with no changes + force
        (
            [test_device],
            event.EventType.RESOURCE_UPDATED,
            test_device.id,
            event.AferoEvent(
                type=event.EventType.RESOURCE_UPDATED,
                device_id=test_device.id,
                device=test_device,
                force_forward=True,
            ),
            {test_device.id},
            replace(test_res),
        ),
        # Device deleted
        (
            [test_device],
            event.EventType.RESOURCE_DELETED,
            test_device.id,
            event.AferoEvent(
                type=event.EventType.RESOURCE_DELETED,
                device_id=test_device.id,
                force_forward=False,
            ),
            set(),
            replace(test_res),
        ),
        # Not a real event
        (
            [],
            event.EventType.RECONNECTED,
            test_device.id,
            event.AferoEvent(
                type=event.EventType.RECONNECTED,
                device_id=test_device.id,
                force_forward=False,
            ),
            set(),
            None,
        ),
    ],
)
async def test__handle_event_type(
    init_elem, evt_type, item_id, evt_data, expected_devs, expected_return, ex1_rc
):
    for elem in init_elem:
        ex1_rc._items[elem.id] = await ex1_rc.initialize_elem(elem)
        ex1_rc._bridge.add_device(elem.id, ex1_rc)
    assert (
        await ex1_rc._handle_event_type(evt_type, item_id, evt_data) == expected_return
    )
    if expected_return and evt_type != event.EventType.RESOURCE_DELETED:
        assert item_id in ex1_rc
    assert ex1_rc._bridge.tracked_devices == expected_devs


@pytest.mark.asyncio
@pytest.mark.parametrize("is_coroutine", [True, False])
@pytest.mark.parametrize(
    "id_filter, event_filter, event_type, expected",
    [
        ("beans", event.EventType.RESOURCE_ADDED, event.EventType.RESOURCE_ADDED, True),
        (
            "beans",
            event.EventType.RESOURCE_ADDED,
            event.EventType.RESOURCE_UPDATED,
            False,
        ),
        (
            "not-a-bean",
            event.EventType.RESOURCE_ADDED,
            event.EventType.RESOURCE_ADDED,
            False,
        ),
    ],
)
async def test_emit_to_subscribers(
    is_coroutine, id_filter, event_filter, event_type, expected, ex1_rc, mocker
):

    callback = mocker.AsyncMock() if is_coroutine else mocker.Mock()
    ex1_rc.subscribe(callback, id_filter=id_filter, event_filter=event_filter)
    await ex1_rc.emit_to_subscribers(event_type, "beans", test_res)
    if expected:
        callback.assert_called_once()
    else:
        callback.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "evt_type, evt_data, called",
    [
        # No data
        (event.EventType.RECONNECTED, None, False),
        # data
        (
            event.EventType.RESOURCE_DELETED,
            event.AferoEvent(
                type=event.EventType.RESOURCE_DELETED,
                device_id=test_device.id,
                force_forward=False,
            ),
            True,
        ),
        # data but not an item
        (
            event.EventType.RESOURCE_UPDATED,
            event.AferoEvent(
                type=event.EventType.RESOURCE_UPDATED,
                device_id="no-thanks",
                device=test_device,
                force_forward=True,
            ),
            False,
        ),
    ],
)
async def test__handle_event(evt_type, evt_data, called, ex1_rc, mocker):
    ex1_rc._items[test_device.id] = await ex1_rc.initialize_elem(test_device)
    ex1_rc._bridge.add_device(test_device.id, ex1_rc)
    emitted = mocker.patch.object(ex1_rc, "emit_to_subscribers")
    await ex1_rc._handle_event(evt_type, evt_data)
    if called:
        emitted.assert_called_once()
    else:
        emitted.assert_not_called()


def mocked_get_filtered_devices(initial_data) -> list[AferoDevice]:
    valid = []
    for ind, element in enumerate(initial_data):
        if element["typeId"] != models.ResourceTypes.DEVICE.value:
            continue
        if ind % 2 == 0:
            valid.append(get_afero_device(element))
    return valid


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "get_filtered_devices, expected_ids",
    [
        (
            False,
            {
                "99a03fb7-ebaa-4fc2-a7b5-df223003b127",
                "84338ebe-7ddf-4bfa-9753-3ee8cdcc8da6",
                "bc429efe-592a-4852-a18b-5b2a5e6ca5f1",
            },
        ),
        (
            mocked_get_filtered_devices,
            {
                "b16fc78d-4639-41a7-8a10-868405c412d6",
                "84338ebe-7ddf-4bfa-9753-3ee8cdcc8da6",
                "b50d9823-7ba0-44d9-b9a9-ad64dbbb225f",
            },
        ),
    ],
)
async def test__get_valid_devices(get_filtered_devices, expected_ids, ex1_rc):
    data = utils.get_raw_dump("raw_hs_data.json")
    if get_filtered_devices:
        ex1_rc.get_filtered_devices = get_filtered_devices
    devices = await ex1_rc._get_valid_devices(data)
    assert len(devices) == len(expected_ids)
    for device in devices:
        assert device.id in expected_ids


@pytest.mark.asyncio
async def test_initialize_not_needed(ex1_rc, mocker):
    check = mocker.patch.object(ex1_rc, "_get_valid_devices")
    ex1_rc._initialized = True
    await ex1_rc.initialize()
    check.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("item_types", [True])
async def test_initialize(item_types, ex1_rc, mocker):
    ex1_rc._initialized = False
    handle_event = mocker.patch.object(ex1_rc, "_handle_event")
    await ex1_rc.initialize()
    assert len(ex1_rc._bridge.events._subscribers) == 14
    assert "nada" in ex1_rc._bridge.events.registered_multiple_devices
    assert ex1_rc._bridge.events.registered_multiple_devices["nada"] == callback


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "state",
        "expected_name",
        "expected_unit",
    ),
    [
        (
            AferoState(
                functionClass="yup",
                functionInstance=None,
                value=60,
            ),
            "disp",
            "unit",
        ),
        (
            AferoState(
                functionClass="nope",
                functionInstance=None,
                value=60,
            ),
            "nope",
            "unit",
        ),
        (
            AferoState(
                functionClass="nope",
                functionInstance="nope",
                value=60,
            ),
            "nope-nope",
            "unit",
        ),
    ],
)
async def test_initialize_number(state, expected_name, expected_unit, ex1_rc):
    func_def = {"values": [{"range": {"min": 60, "max": 1800, "step": 60}}]}
    _, number = await ex1_rc.initialize_number(func_def, state)
    assert number == NumbersFeature(
        value=state.value,
        min=60,
        max=1800,
        step=60,
        name=expected_name,
        unit=expected_unit,
    )


@pytest.mark.parametrize(
    "id_filter, event_filter, expected, expected_unsub",
    [
        # No ID filter
        (None, None, {"*": [(min, None)]}, {"*": []}),
        # ID filter
        ("beans", None, {"*": [], "beans": [(min, None)]}, {"*": [], "beans": []}),
        # ID filter as a tuple
        (
            ("beans", "double_beans"),
            (event.EventType.RESOURCE_ADDED,),
            {
                "*": [],
                "beans": [(min, (event.EventType.RESOURCE_ADDED,))],
                "double_beans": [(min, (event.EventType.RESOURCE_ADDED,))],
            },
            {"*": [], "beans": [], "double_beans": []},
        ),
    ],
)
def test_subscribe(id_filter, event_filter, expected, expected_unsub, ex1_rc):
    unsub = ex1_rc.subscribe(min, id_filter=id_filter, event_filter=event_filter)
    assert ex1_rc._subscribers == expected
    unsub()
    assert ex1_rc._subscribers == expected_unsub


def test_subscribe_with_starting(ex1_rc):
    ex1_rc.subscribe(min, id_filter="cool")
    unsub2 = ex1_rc.subscribe(min, id_filter="cool2")
    assert ex1_rc._subscribers == {
        "*": [],
        "cool": [(min, None)],
        "cool2": [(min, None)],
    }
    unsub2()
    assert ex1_rc._subscribers == {"*": [], "cool": [(min, None)], "cool2": []}


@pytest.mark.asyncio
async def test__process_state_update(ex1_rc):
    ex1_rc._items[test_res.id] = await ex1_rc.initialize_elem(test_device)
    ex1_rc._bridge.add_device(test_res.id, ex1_rc)
    await ex1_rc._process_state_update(
        ex1_rc._items[test_res.id],
        test_res.id,
        [
            {
                "functionClass": "mapped_beans",
                "value": "off",
                "lastUpdateTime": 0,
                "functionInstance": "bean2",
            }
        ],
    )
    assert ex1_rc._items[test_res.id].beans["bean2"].on is False
    update_req = await ex1_rc._bridge.events._event_queue.get()
    assert update_req["device"].id == "cool"
    assert update_req["device_id"] == "cool"
    assert update_req["force_forward"] is True
    assert update_req["type"] == event.EventType.RESOURCE_UPDATED
    state_update = update_req["device"].states[0]
    assert state_update.functionClass == "mapped_beans"
    assert state_update.functionInstance == "bean2"
    assert state_update.value == "off"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("temperature_unit"),
    [
        (TemperatureUnit.CELSIUS),
        (TemperatureUnit.FAHRENHEIT),
    ]
)
@pytest.mark.parametrize(
    "response, response_err, states, expected_call, expected, messages",
    [
        # Happy path
        (
            {"status": 200},
            None,
            [
                {
                    "functionClass": "mapped_beans",
                    "value": "off",
                    "lastUpdateTime": 0,
                    "functionInstance": "bean2",
                }
            ],
            {
                "json": {
                    "metadeviceId": "cool",
                    "values": [
                        {
                            "functionClass": "mapped_beans",
                            "value": "off",
                            "lastUpdateTime": 0,
                            "functionInstance": "bean2",
                        }
                    ],
                },
                "headers": {
                    "host": v1_const.AFERO_CLIENTS["hubspace"]["API_DATA_HOST"],
                    "content-type": "application/json; charset=utf-8",
                },
                "params": {},
            },
            True,
            [],
        ),
        # Failed update
        (
            {"status": 400},
            None,
            [
                {
                    "functionClass": "mapped_beans",
                    "value": "off",
                    "lastUpdateTime": 0,
                    "functionInstance": "bean2",
                }
            ],
            {
                "json": {
                    "metadeviceId": "cool",
                    "values": [
                        {
                            "functionClass": "mapped_beans",
                            "value": "off",
                            "lastUpdateTime": 0,
                            "functionInstance": "bean2",
                        }
                    ],
                },
                "headers": {
                    "host": v1_const.AFERO_CLIENTS["hubspace"]["API_DATA_HOST"],
                    "content-type": "application/json; charset=utf-8",
                },
                "params": {},
            },
            False,
            ["Invalid update provided for cool using"],
        ),
        # Retry exception
        (
            None,
            ExceededMaximumRetries,
            [
                {
                    "functionClass": "mapped_beans",
                    "value": "off",
                    "lastUpdateTime": 0,
                    "functionInstance": "bean2",
                }
            ],
            {
                "json": {
                    "metadeviceId": "cool",
                    "values": [
                        {
                            "functionClass": "mapped_beans",
                            "value": "off",
                            "lastUpdateTime": 0,
                            "functionInstance": "bean2",
                        }
                    ],
                },
                "headers": {
                    "host": v1_const.AFERO_CLIENTS["hubspace"]["API_DATA_HOST"],
                    "content-type": "application/json; charset=utf-8",
                },
                "params": {},
            },
            False,
            ["Maximum retries exceeded for cool"],
        ),
    ],
)
async def test_update_afero_api(
    temperature_unit,
    response,
    response_err,
    states,
    expected_call,
    expected,
    messages,
    ex1_rc,
    mock_aioresponse,
    caplog,
):
    device_id = "cool"
    ex1_rc._bridge.temperature_unit = temperature_unit
    mock_response_url = ex1_rc._bridge.generate_api_url(v1_const.AFERO_GENERICS["API_DEVICE_STATE_ENDPOINT"].format(
        ex1_rc._bridge.account_id, str(device_id)
    ))
    query_url = mock_response_url[:]
    if temperature_unit == TemperatureUnit.FAHRENHEIT:
        expected_call["params"]["units"] = temperature_unit.value
        mock_response_url = f"{mock_response_url}?units={temperature_unit.value}"
    else:
        # There is something weird with the tests where this is leaking from previous tests
        expected_call["params"].pop("units", None)
    if response:
        mock_aioresponse.put(mock_response_url, **response)
    if response_err:
        ex1_rc._bridge.request.side_effect = response_err
    if expected:
        assert await ex1_rc.update_afero_api(device_id, states) is not False
    else:
        assert await ex1_rc.update_afero_api(device_id, states) == expected
    if expected_call:
        
        ex1_rc._bridge.request.assert_called_with("put", query_url, **expected_call)
    else:
        ex1_rc._bridge.request.assert_not_called()
    for message in messages:
        assert message in caplog.text


@pytest.mark.asyncio
async def test_update_dev_not_found(ex1_rc, caplog):
    caplog.set_level(logging.DEBUG)
    await ex1_rc.update("not-a-device")
    assert "Unable to update device not-a-device as it does not exist" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "obj_in, states, expected_states, expected_item, successful",
    [
        # Obj in without updates
        (TestResourcePut(on=None, beans=None), None, None, test_res, True),
        # Obj in with updates
        (
            TestResourcePut(
                on=None, beans=TestFeatureInstance(on=True, func_instance="bean2")
            ),
            None,
            [
                {
                    "functionClass": "mapped_beans",
                    "functionInstance": "bean2",
                    "value": "on",
                    "lastUpdateTime": 12345,
                }
            ],
            test_res_update,
            True,
        ),
        # Obj in with unsuccessful updates
        (
            TestResourcePut(
                on=None, beans=TestFeatureInstance(on=True, func_instance="bean2")
            ),
            None,
            [
                {
                    "functionClass": "mapped_beans",
                    "functionInstance": "bean2",
                    "value": "on",
                    "lastUpdateTime": 12345,
                }
            ],
            test_res,
            False,
        ),
        # Manual states
        (
            None,
            [
                {
                    "functionClass": "mapped_beans",
                    "functionInstance": "bean2",
                    "value": "on",
                    "lastUpdateTime": 123456,
                }
            ],
            [
                {
                    "functionClass": "mapped_beans",
                    "functionInstance": "bean2",
                    "value": "on",
                    "lastUpdateTime": 123456,
                }
            ],
            test_res_update,
            True,
        ),
    ],
)
async def test_update(
    obj_in, states, expected_states, expected_item, successful, ex1_rc_mocked, mocker
):
    ex1_rc = ex1_rc_mocked
    await ex1_rc.initialize()
    mocker.patch("time.time", return_value=12345)
    await ex1_rc._bridge.events.generate_events_from_data(
        [utils.create_hs_raw_from_device(test_device)]
    )
    await ex1_rc._bridge.async_block_until_done()
    if successful:
        resp = mocker.AsyncMock()
        resp.status = 200
        json_resp = mocker.AsyncMock()
        json_resp.return_value = {"metadeviceId": test_device.id, "values": expected_states}
        resp.json = json_resp
        update_afero_api = mocker.patch.object(
            ex1_rc, "update_afero_api", return_value=resp
        )
    else:
        update_afero_api = mocker.patch.object(
            ex1_rc, "update_afero_api", return_value=False
        )
    await ex1_rc.update(test_device.id, obj_in=obj_in, states=states)
    if not expected_states:
        update_afero_api.assert_not_called()
    else:
        update_afero_api.assert_called_once_with(test_device.id, expected_states)
    await ex1_rc._bridge.async_block_until_done()
    assert ex1_rc._items[test_device.id] == expected_item


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device, obj_in, states, expected_states, expected_item, successful",
    [
        (
            test_device_dict,
            TestResourceDictPut(
                selects={
                    ("b1", None): SelectFeature(
                        selected="False", selects={"True", "False"}, name="b1"
                    ),
                    ("b2", "one"): SelectFeature(
                        selected="cool", selects={"beans", "cool"}, name="b2-1"
                    ),
                    ("b2", "two"): SelectFeature(
                        selected="beans", selects={"beans", "cool"}, name="b2-2"
                    ),
                },
            ),
            None,
            [
                {
                    "functionClass": "b1",
                    "functionInstance": None,
                    "value": "False",
                    "lastUpdateTime": 12345,
                },
                {
                    "functionClass": "b2",
                    "functionInstance": "one",
                    "value": "cool",
                    "lastUpdateTime": 12345,
                },
                {
                    "functionClass": "b2",
                    "functionInstance": "two",
                    "value": "beans",
                    "lastUpdateTime": 12345,
                },
            ],
            test_res_update_dict,
            True,
        ),
    ],
)
async def test_update_dict(
    device, obj_in, states, expected_states, expected_item, successful, ex2_rc_mocked, mocker
):
    ex2_rc = ex2_rc_mocked
    await ex2_rc.initialize()
    mocker.patch("time.time", return_value=12345)
    ex2_rc._items[device.id] = await ex2_rc.initialize_elem(device)
    ex2_rc._bridge.add_device(device.id, ex2_rc)
    ex2_rc._bridge.add_afero_dev(device)
    if successful:
        json_resp = mocker.AsyncMock(return_value={"metadeviceId": test_device.id, "values": expected_states})
    else:
        json_resp = mocker.AsyncMock(return_value=False)
    resp = mocker.AsyncMock()
    resp.json = json_resp
    update_afero_api = mocker.patch.object(
        ex2_rc, "update_afero_api", return_value=resp
    )
    await ex2_rc.update(device.id, obj_in=obj_in, states=states)
    if not expected_states:
        update_afero_api.assert_not_called()
    else:
        update_afero_api.assert_called_once_with(device.id, expected_states)
    await ex2_rc._bridge.async_block_until_done()
    assert ex2_rc._items[device.id] == expected_item


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "starting_items,device_id,expected",
    [
        ({"cool": "beans"}, "not-a-device", None),
        ({"cool": "beans"}, "cool", "beans"),
    ],
)
async def test_get_device(ex1_rc, starting_items, device_id, expected):
    ex1_rc._items = starting_items
    if not expected:
        with pytest.raises(DeviceNotFound):
            ex1_rc.get_device(device_id)
    else:
        assert ex1_rc.get_device(device_id) == expected


async def callback_test(elem, update_vals: dataclass):
    for f in fields(update_vals):
        if f.name == "callback":
            continue
        cur_val = getattr(update_vals, f.name, None)
        elem_val = getattr(elem, f.name)
        if cur_val is None:
            continue
        # There is probably a better way to approach this
        if not str(f.type).startswith("dict"):
            # Special processing for dicts
            if isinstance(elem_val, dict):
                cur_val = {getattr(cur_val, "func_instance", None): cur_val}
                getattr(elem, f.name).update(cur_val)
            else:
                setattr(elem, f.name, cur_val)
        else:
            elem_val.update(cur_val)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("elem", "update_obj", "mapping", "send_duplicate_states", "expected"),
    [
        # Empty
        (
            replace(test_res_default_dict),
            TestResourceDictPut(selects={}),
            {},
            False,
            [],
        ),
        # Dont match each other - test continue
        (
            replace(test_res_default_dict),
            TestResourcePut(on=None, beans=None),
            {},
            False,
            [],
        ),
        # No updates
        (
            replace(test_res_default_dict),
            TestResourceDictPut(
                selects={
                    ("b2", "two"): SelectFeature(
                        selected="cool", selects={"beans", "cool"}, name="b2-2"
                    ),
                }
            ),
            {},
            False,
            [],
        ),
        # Test dict mapping
        (
            replace(test_res_default_dict),
            TestResourceDictPut(
                selects={
                    ("b1", None): SelectFeature(
                        selected="False", selects={"True", "False"}, name="b1"
                    ),
                    ("b2", "one"): SelectFeature(
                        selected="cool", selects={"beans", "cool"}, name="b2-1"
                    ),
                    ("b2", "two"): SelectFeature(
                        selected="beans", selects={"beans", "cool"}, name="b2-2"
                    ),
                },
            ),
            {},
            False,
            [
                {
                    "functionClass": "b1",
                    "functionInstance": None,
                    "value": "False",
                    "lastUpdateTime": 12345,
                },
                {
                    "functionClass": "b2",
                    "functionInstance": "one",
                    "value": "cool",
                    "lastUpdateTime": 12345,
                },
                {
                    "functionClass": "b2",
                    "functionInstance": "two",
                    "value": "beans",
                    "lastUpdateTime": 12345,
                },
            ],
        ),
        # Test non-dict mapping
        (
            replace(test_res),
            TestResourcePut(
                on=False, beans=TestFeatureInstance(on=True, func_instance="bean2")
            ),
            {"on": "power"},
            False,
            [
                {
                    "functionClass": "power",
                    "functionInstance": None,
                    "lastUpdateTime": 12345,
                    "value": False,
                },
                {
                    "value": "on",
                    "functionClass": "mapped_beans",
                    "functionInstance": "bean2",
                    "lastUpdateTime": 12345,
                },
            ],
        ),
        # Testing a list
        (
            TestResourceList(the_beans=ReturnsAListFeature(useless_value=True)),
            TestResourceListPut(the_beans=ReturnsAListFeature(useless_value=False)),
            {},
            False,
            [
                {
                    "value": "cool",
                    "functionClass": "bean-type",
                    "functionInstance": "temperature",
                    "lastUpdateTime": 12345,
                },
                {
                    "value": "bean",
                    "functionClass": "bean-type",
                    "functionInstance": "warmth",
                    "lastUpdateTime": 12345,
                },
            ],
        ),
        # Testing when a value does not change
        (
            TestResourceList(the_beans=ReturnsAListFeature(useless_value=True)),
            TestResourceListPut(the_beans=ReturnsAListFeature(useless_value=True)),
            {},
False,
            [],
        ),
        # Test duplicates
        (
            replace(test_res_default_dict),
            TestResourceDictPut(
                selects={
                    ("b2", "two"): SelectFeature(
                        selected="cool", selects={"beans", "cool"}, name="b2-2"
                    ),
                }
            ),
            {},
            True,
             [
                 {
                     'functionClass': 'b2',
                     'functionInstance': 'two',
                     'lastUpdateTime': 12345,
                     'value': 'cool',
                    },
                ]
        ),
    ],
)
def test_dataclass_to_afero(elem, update_obj, mapping, send_duplicate_states, expected, mocker):
    mocker.patch("time.time", return_value=12345)
    assert dataclass_to_afero(elem, update_obj, mapping, send_duplicate_states) == expected


@pytest.mark.parametrize(
    ("element", "field_name", "update_vals", "send_duplicate_states", "expected"),
    [
        # Dont send dupes
        (
            replace(test_res_default_dict),
            "selects",
            {
                ("b1", None): SelectFeature(
                    selected="False", selects={"True", "False"}, name="b1"
                ),
                ("b2", "one"): SelectFeature(
                    selected="beans", selects={"beans", "cool"}, name="b2-1"
                ),
                ("b2", "two"): SelectFeature(
                    selected="beans", selects={"beans", "cool"}, name="b2-2"
                ),
            },
            False,
            [
                {
                    "functionClass": "b1",
                    "functionInstance": None,
                    "value": "False",
                    "lastUpdateTime": 12345,
                },
                {
                    "functionClass": "b2",
                    "functionInstance": "two",
                    "value": "beans",
                    "lastUpdateTime": 12345,
                },
            ],
        ),
        # Send dupes
(
            replace(test_res_default_dict),
            "selects",
            {
                ("b1", None): SelectFeature(
                    selected="False", selects={"True", "False"}, name="b1"
                ),
                ("b2", "one"): SelectFeature(
                    selected="beans", selects={"beans", "cool"}, name="b2-1"
                ),
                ("b2", "two"): SelectFeature(
                    selected="beans", selects={"beans", "cool"}, name="b2-2"
                ),
            },
            True,
            [
                {
                    "functionClass": "b1",
                    "functionInstance": None,
                    "value": "False",
                    "lastUpdateTime": 12345,
                },
{
                    "functionClass": "b2",
                    "functionInstance": "one",
                    "value": "beans",
                    "lastUpdateTime": 12345,
                },
                {
                    "functionClass": "b2",
                    "functionInstance": "two",
                    "value": "beans",
                    "lastUpdateTime": 12345,
                },
            ],
        )
    ],
)
def test_get_afero_states_from_mapped(
    element, field_name, update_vals, send_duplicate_states, expected, mocker
):
    mocker.patch("time.time", return_value=12345)
    assert get_afero_states_from_mapped(element, field_name, update_vals, send_duplicate_states) == expected


@pytest.mark.parametrize(
    "elem, feat, mapped_afero_key, expected",
    [
        # Utilize func_instance
        (test_res, TestFeatureInstance(on=True, func_instance="bean1"), None, "bean1"),
        # Utilize instances
        (test_res_funcs, TestFeatureBool(on=True), "on", "super-beans"),
        # None fallback
        (test_res_funcs, TestFeatureBool(on=True), None, None),
    ],
)
def test_get_afero_instance_for_state(elem, feat, mapped_afero_key, expected, mocker):
    mocker.patch("time.time", return_value=12345)
    assert get_afero_instance_for_state(elem, feat, mapped_afero_key) == expected


@pytest.mark.parametrize(
    "func_class, func_instance, current_val, expected",
    [
        # Non-dict val
        (
            "cool",
            "beans",
            "super-beans",
            {
                "functionClass": "cool",
                "functionInstance": "beans",
                "lastUpdateTime": 12345,
                "value": "super-beans",
            },
        ),
        # dict val
        (
            "cool",
            "beans",
            {"functionClass": "beans", "functionInstance": "cool", "value": 12},
            {
                "functionClass": "beans",
                "functionInstance": "cool",
                "lastUpdateTime": 12345,
                "value": 12,
            },
        ),
    ],
)
def test_get_afero_state_from_feature(
    func_class, func_instance, current_val, expected, mocker
):
    mocker.patch("time.time", return_value=12345)
    assert (
        get_afero_state_from_feature(func_class, func_instance, current_val) == expected
    )


@pytest.mark.parametrize(
    "states, expected",
    [
        (
            [
                {
                    "functionClass": "beans",
                    "functionInstance": "cool",
                    "value": 12,
                },
                {
                    "functionClass": "beans",
                    "functionInstance": "cool2",
                    "value": 12,
                },
            ],
            [
                {
                    "functionClass": "beans",
                    "functionInstance": "cool",
                    "lastUpdateTime": 12345,
                    "value": 12,
                },
                {
                    "functionClass": "beans",
                    "functionInstance": "cool2",
                    "lastUpdateTime": 12345,
                    "value": 12,
                },
            ],
        )
    ],
)
def test_get_afero_states_from_list(states, expected, mocker):
    mocker.patch("time.time", return_value=12345)
    assert get_afero_states_from_list(states) == expected


def test_unsubscribe(ex1_rc):
    assert ex1_rc._subscribers == {"*": []}

    def whatever(*args, **kwargs):
        pass

    unsub = ex1_rc.subscribe(whatever, id_filter="beans")
    unsub2 = ex1_rc.subscribe(whatever, id_filter="beans2")
    assert ex1_rc._subscribers == {"*": [], "beans": [(whatever, None)], "beans2": [(whatever, None)]}
    ex1_rc._subscribers = {"*": [], "beans": [(whatever, None)]}
    # Ensure no error if unsub called if its somehow removed
    unsub2()
    ex1_rc._subscribers = {"*": [], "beans": [(whatever, None)]}
    unsub()
    assert ex1_rc._subscribers == {"*": [], "beans": []}