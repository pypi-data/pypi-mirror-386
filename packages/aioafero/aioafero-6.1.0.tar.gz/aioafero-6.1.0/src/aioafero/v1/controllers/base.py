"""Base class for Controllers."""

import asyncio
from asyncio.coroutines import iscoroutinefunction
from collections.abc import Callable, Iterator
import contextlib
from dataclasses import dataclass, fields
from datetime import UTC, datetime
import re
import time
from typing import TYPE_CHECKING, Any, Generic, NamedTuple

import aiohttp

from aioafero.device import (
    AferoDevice,
    AferoResource,
    AferoState,
    convert_state,
    get_afero_device,
)
from aioafero.errors import DeviceNotFound, ExceededMaximumRetries
from aioafero.types import TemperatureUnit
from aioafero.util import process_function
from aioafero.v1 import v1_const
from aioafero.v1.models.features import NumbersFeature, SelectFeature
from aioafero.v1.models.resource import ResourceTypes
from aioafero.v1.models.sensor import AferoBinarySensor, AferoSensor

from .event import AferoEvent, EventCallBackType, EventType

if TYPE_CHECKING:  # pragma: no cover
    from aioafero.v1 import AferoBridgeV1


EventSubscriptionType = tuple[
    EventCallBackType,
    "tuple[EventType] | None",
]

ID_FILTER_ALL = "*"

unit_extractor = re.compile(r"(\d*)(\D*)")


class NumbersName(NamedTuple):
    """Data used for displaying a Number."""

    unit: str
    display_name: str | None = None


class BaseResourcesController(Generic[AferoResource]):
    """Base Controller for Afero IoT Cloud devices."""

    ITEM_TYPE_ID: ResourceTypes | None = None
    ITEM_TYPES: list[ResourceTypes] | None = None
    ITEM_CLS = None
    # functionClass map between controller -> Afero IoT Cloud
    ITEM_MAPPING: dict = {}
    # Sensors map functionClass -> Unit
    ITEM_SENSORS: dict[str, str] = {}
    # Binary sensors map key -> alerting value
    ITEM_BINARY_SENSORS: dict[str, str] = {}
    # Elements that map to numbers. func class / func instance to unit
    ITEM_NUMBERS: dict[tuple[str, str | None], NumbersName] = {}
    # Elements that map to selects func class / func instance to name
    ITEM_SELECTS: dict[tuple[str, str | None], str] = {}
    # Device Split Callbacks
    DEVICE_SPLIT_CALLBACKS: dict[str, callable] = {}

    def __init__(self, bridge: "AferoBridgeV1") -> None:
        """Initialize instance."""
        self._bridge = bridge
        self._items: dict[str, AferoResource] = {}
        self._logger = bridge.logger.getChild(self.ITEM_CLS.__name__)
        self._subscribers: dict[str, list[EventSubscriptionType]] = {ID_FILTER_ALL: []}
        self._initialized: bool = False
        self._item_values = [x.value for x in self.ITEM_TYPES]

    def __getitem__(self, device_id: str) -> AferoResource:
        """Get item by device_id."""
        return self._items[device_id]

    def __iter__(self) -> Iterator[AferoResource]:
        """Iterate items."""
        return iter(self._items.values())

    def __contains__(self, device_id: str) -> bool:
        """Return bool if device_id is in items."""
        return device_id in self._items

    @property
    def items(self) -> list[AferoResource]:
        """Return all items for this resource."""
        return list(self._items.values())

    @property
    def initialized(self) -> bool:
        """Determine if the controller has been initialized."""
        return self._initialized

    @property
    def subscribers(self) -> dict[str, list[EventSubscriptionType]]:
        """Get all subscribers aligned to this controller."""
        return self._subscribers

    async def _handle_event(
        self, evt_type: EventType, evt_data: AferoEvent | None
    ) -> None:
        """Handle incoming event for this resource."""
        if evt_data is None:
            return
        item_id = evt_data.get("device_id", None)
        cur_item = await self._handle_event_type(evt_type, item_id, evt_data)
        if evt_type == EventType.RESOURCE_UPDATE_RESPONSE:
            evt_type = EventType.RESOURCE_UPDATED
        if cur_item:
            await self.emit_to_subscribers(evt_type, item_id, cur_item)

    async def _handle_event_type(
        self, evt_type: EventType, item_id: str, evt_data: AferoEvent
    ) -> AferoResource | list[AferoResource] | None:
        """Determine what to do with the incoming event.

        :param evt_type: Type of event
        :param item_id: ID of the item
        :param evt_data: Event data

        :return: Item after being processed
        """
        if evt_type == EventType.RESOURCE_ADDED:
            self._logger.info(
                "Initializing %s [%s] as a %s",
                evt_data["device"].friendly_name,
                evt_data["device"].id,
                self.ITEM_CLS.__name__,
            )
            cur_item = await self.initialize_elem(evt_data["device"])
            self._items[item_id] = cur_item
            self._bridge.add_device(evt_data["device"].id, self)
        elif evt_type == EventType.RESOURCE_DELETED:
            cur_item = self._items.pop(item_id, evt_data)
            self._bridge.remove_device(evt_data["device_id"])
        elif evt_type in [
            EventType.RESOURCE_UPDATED,
            EventType.RESOURCE_UPDATE_RESPONSE,
        ]:
            # existing item updated
            try:
                cur_item = self.get_device(item_id)
            except DeviceNotFound:
                return None
            if not await self.update_elem(evt_data["device"]) and not evt_data.get(
                "force_forward", False
            ):
                return None
        else:
            # Skip all other events
            return None
        return cur_item

    async def emit_to_subscribers(
        self, evt_type: EventType, item_id: str, item: AferoResource
    ):
        """Emit updates to subscribers.

        :param evt_type: Type of event
        :param item_id: ID of the item
        :param item: Item to emit to subscribers
        """
        subscribers = (
            self._subscribers.get(item_id, []) + self._subscribers[ID_FILTER_ALL]
        )
        for callback, event_filter in subscribers:
            if event_filter is not None and evt_type not in event_filter:
                continue
            # dispatch the full resource object to the callback
            if iscoroutinefunction(callback):
                self._bridge.add_job(asyncio.create_task(callback(evt_type, item)))
            else:
                callback(evt_type, item)

    def get_filtered_devices(self, initial_data: list[dict]) -> list[AferoDevice]:
        """Determine devices that align to the controller."""
        valid_devices: list[AferoDevice] = []
        for element in initial_data:
            if element["typeId"] != self.ITEM_TYPE_ID.value:
                self._logger.debug(
                    "TypeID [%s] does not match %s",
                    element["typeId"],
                    self.ITEM_TYPE_ID.value,
                )
                continue
            device = get_afero_device(element)
            if device.device_class not in self._item_values:
                self._logger.debug(
                    "Device Class [%s] is not contained in %s",
                    device.device_class,
                    self._item_values,
                )
                continue
            valid_devices.append(device)
        return valid_devices

    async def _get_valid_devices(self, initial_data: list[dict]) -> list[AferoDevice]:
        return self.get_filtered_devices(initial_data)

    async def initialize(self) -> None:
        """Initialize controller the controller.

        Initialization process should only occur once. During this process, it will
        subscribe to all updates for the given resources and register any device
        split callbacks for the event controller.
        """
        if self._initialized:
            return
        # subscribe to item updates
        res_filter = tuple(x.value for x in self.ITEM_TYPES)
        self._bridge.events.subscribe(
            self._handle_event,
            resource_filter=res_filter,
        )
        for name, callback in self.DEVICE_SPLIT_CALLBACKS.items():
            self._bridge.events.register_multi_device(name, callback)
        self._initialized = True

    async def initialize_number(
        self, func_def: dict, state: AferoState
    ) -> tuple[tuple[str, str | None], NumbersFeature] | None:
        """Initialize a number from the provided data."""
        key = (state.functionClass, state.functionInstance)
        if key in self.ITEM_NUMBERS:
            working_def = func_def["values"][0]
            primary_name = self.ITEM_NUMBERS[key].display_name
            if primary_name is None:
                fallback_name = f"{state.functionClass}"
                if state.functionInstance is not None:
                    fallback_name += f"-{state.functionInstance}"
                primary_name = working_def.get("name", fallback_name)
            return key, NumbersFeature(
                value=state.value,
                min=working_def["range"]["min"],
                max=working_def["range"]["max"],
                step=working_def["range"]["step"],
                name=primary_name,
                unit=self.ITEM_NUMBERS[key].unit,
            )
        return None

    async def initialize_select(
        self, functions: list[dict], state: AferoState
    ) -> tuple[tuple[str, str | None], SelectFeature] | None:
        """Initialize a select from the provided data."""
        key = (state.functionClass, state.functionInstance)
        if key in self.ITEM_SELECTS:
            return key, SelectFeature(
                selected=state.value,
                selects=set(
                    process_function(
                        functions, state.functionClass, state.functionInstance
                    )
                ),
                name=self.ITEM_SELECTS[key],
            )
        return None

    async def initialize_sensor(
        self, state: AferoState, child_id: str
    ) -> AferoSensor | AferoBinarySensor | None:
        """Initialize the sensor.

        :param state: State to update
        :param child_id: device_id of the parent device
        """
        if state.functionClass in self.ITEM_SENSORS:
            value, unit = await self.split_sensor_data(state)
            return AferoSensor(
                id=state.functionClass,
                owner=child_id,
                value=value,
                unit=unit,
            )
        if state.functionClass in self.ITEM_BINARY_SENSORS:
            value, _ = await self.split_sensor_data(state)
            key = f"{state.functionClass}|{state.functionInstance}"
            return AferoBinarySensor(
                id=key,
                owner=child_id,
                instance=state.functionInstance,
                current_value=value,
                _error=self.ITEM_BINARY_SENSORS[state.functionClass],
            )
        return None

    async def update_number(
        self, state: AferoState, cur_item: AferoResource
    ) -> str | None:
        """Update the number if its tracked and a change has been detected.

        :param state: State to update
        :param cur_item: Current item to update
        :return: Identifier of the number that was updated or None
        """
        key = (state.functionClass, state.functionInstance)
        if key in self.ITEM_NUMBERS:
            if cur_item.numbers[key].value != state.value:
                cur_item.numbers[key].value = state.value
                return f"number-{key}"
        return None

    async def update_select(
        self, state: AferoState, cur_item: AferoResource
    ) -> str | None:
        """Update the select if its tracked and a change has been detected.

        :param state: State to update
        :param cur_item: Current item to update
        :return: Identifier of the select that was updated or None
        """
        key = (state.functionClass, state.functionInstance)
        if key in self.ITEM_SELECTS:
            if cur_item.selects[key].selected != state.value:
                cur_item.selects[key].selected = state.value
                return f"select-{key}"
        return None

    async def update_sensor(
        self, state: AferoState, cur_item: AferoResource
    ) -> str | None:
        """Update the sensor if its tracked and a change has been detected.

        :param state: State to update
        :param cur_item: Current item to update
        :return: Identifier of the sensor that was updated or None
        """
        if state.functionClass in self.ITEM_SENSORS:
            value, _ = await self.split_sensor_data(state)
            if cur_item.sensors[state.functionClass].value != value:
                cur_item.sensors[state.functionClass].value = value
                return f"sensor-{state.functionClass}"
        elif state.functionClass in self.ITEM_BINARY_SENSORS:
            value, _ = await self.split_sensor_data(state)
            key = f"{state.functionClass}|{state.functionInstance}"
            if cur_item.binary_sensors[key].current_value != value:
                cur_item.binary_sensors[key].current_value = value
                return f"binary-{key}"
        return None

    async def split_sensor_data(self, state: AferoState) -> tuple[Any, str | None]:
        """Split the sensor value and return a tuple of the sensor value and key."""
        if isinstance(state.value, str):
            match = unit_extractor.match(state.value)
            if match and match.group(1) and match.group(2):
                return int(match.group(1)), match.group(2)
        return state.value, self.ITEM_SENSORS.get(state.functionClass, None)

    async def initialize_elem(self, element: AferoDevice) -> None:  # pragma: no cover
        """Initialize the element.

        :param afero_device: Afero Device that contains the updated states

        :return: Newly initialized resource
        """
        raise NotImplementedError("Class should implement initialize_elem")

    async def update_elem(self, element: AferoDevice) -> None:  # pragma: no cover
        """Update the Portable AC with the latest API data.

        :param afero_device: Afero Device that contains the updated states

        :return: States that have been modified
        """
        raise NotImplementedError("Class should implement update_elem")

    def subscribe(
        self,
        callback: EventCallBackType,
        id_filter: str | tuple[str] | None = None,
        event_filter: EventType | tuple[EventType] | None = None,
    ) -> Callable:
        """Subscribe to status changes for this resource type.

        :param callback: callback function to call when an event emits.
        :param id_filter: Optionally provide resource ID(s) to filter events for.
        :param event_filter: Optionally provide EventType(s) as filter.

        Returns:
            function to unsubscribe.

        """
        if not isinstance(event_filter, None | list | tuple):
            event_filter = (event_filter,)

        if id_filter is None:
            id_filter = (ID_FILTER_ALL,)
        elif not isinstance(id_filter, list | tuple):
            id_filter = (id_filter,)

        subscription = (callback, event_filter)

        for id_key in id_filter:
            if id_key not in self._subscribers:
                self._subscribers[id_key] = []
            self._subscribers[id_key].append(subscription)

        # unsubscribe logic
        def unsubscribe():
            for id_key in id_filter:
                if id_key not in self._subscribers:
                    continue
                self._subscribers[id_key].remove(subscription)

        return unsubscribe

    async def _process_state_update(
        self, cur_item: AferoResource, device_id: str, states: list[dict]
    ) -> None:
        dev_states = [
            AferoState(
                functionClass=state["functionClass"],
                value=state["value"],
                functionInstance=state.get("functionInstance"),
                lastUpdateTime=int(datetime.now(UTC).timestamp() * 1000),
            )
            for state in states
        ]
        dummy_update = AferoDevice(
            id=device_id,
            device_id=cur_item.device_information.parent_id,
            model=cur_item.device_information.model,
            device_class=cur_item.device_information.device_class,
            default_image=cur_item.device_information.default_image,
            default_name=cur_item.device_information.default_name,
            friendly_name=cur_item.device_information.name,
            states=dev_states,
        )
        # Update now, but also trigger all chained updates
        await self.update_elem(dummy_update)
        self._bridge.events.add_job(
            AferoEvent(
                type=EventType.RESOURCE_UPDATED,
                device_id=device_id,
                device=dummy_update,
                force_forward=True,
            )
        )

    async def update_afero_api(
        self, device_id: str, states: list[dict]
    ) -> aiohttp.ClientResponse | bool:
        """Update Afero IoT API with the new states.

        :param device_id: Afero IoT Device ID
        :param states: States to manually set

        :return: Response if successful, False otherwise.
        """
        url = self._bridge.generate_api_url(
            v1_const.AFERO_GENERICS["API_DEVICE_STATE_ENDPOINT"].format(
                self._bridge.account_id, str(device_id)
            )
        )
        headers = {
            "host": v1_const.AFERO_CLIENTS[self._bridge.afero_client]["API_DATA_HOST"],
            "content-type": "application/json; charset=utf-8",
        }
        payload = {"metadeviceId": str(device_id), "values": states}
        params = {}
        if self._bridge.temperature_unit == TemperatureUnit.FAHRENHEIT:
            params["units"] = TemperatureUnit.FAHRENHEIT.value
        try:
            res = await self._bridge.request(
                "put", url, json=payload, headers=headers, params=params
            )
        except ExceededMaximumRetries:
            self._logger.warning("Maximum retries exceeded for %s", device_id)
            return False
        else:
            # Bad states provided
            if res.status == 400:
                self._logger.warning(
                    "Invalid update provided for %s using %s", device_id, states
                )
                return False
        return res

    async def update(
        self,
        device_id: str,
        obj_in: AferoResource | None = None,
        states: list[dict] | None = None,
        send_duplicate_states: bool = False,
    ) -> aiohttp.ClientResponse | None:
        """Update Afero IoT with the new data.

        :param device_id: Afero IoT Device ID
        :param obj_in: Afero IoT Resource elements to change
        :param states: States to manually set
        :param send_duplicate_states: Send all states, regardless if there's been a change
        """
        update_id = device_id
        try:
            cur_item = self.get_device(device_id)
        except DeviceNotFound:
            self._logger.info(
                "Unable to update device %s as it does not exist", device_id
            )
            return None
        # split devices use <elem>.update_id to specify the correct device id
        with contextlib.suppress(AttributeError):
            update_id = cur_item.update_id
        if obj_in:
            device_states = dataclass_to_afero(
                cur_item, obj_in, self.ITEM_MAPPING, send_duplicate_states
            )
            if not device_states:
                self._logger.debug("No states to send. Skipping")
                return None
        else:  # Manually setting states
            device_states = states
        # @TODO - Implement bluetooth logic for update
        if res := await self.update_afero_api(update_id, device_states):
            resp_json = await res.json()
            states = [convert_state(val) for val in resp_json.get("values", [])]
            update_dev = self.generate_update_dev(resp_json["metadeviceId"], states)
            update_dev.id = update_id
            await self._bridge.events.generate_events_from_update(update_dev)
            return res
        return None

    def generate_update_dev(self, device_id: str, states: list[AferoState]) -> dict:
        """Generate update data for the event controller."""
        afero_dev = self._bridge.get_afero_device(device_id)
        afero_dev.states = states
        return afero_dev

    def get_device(self, device_id) -> AferoResource:
        """Lookup the device with the given ID."""
        try:
            return self[device_id]
        except KeyError as err:
            raise DeviceNotFound(device_id) from err


def dataclass_to_afero(
    elem: AferoResource, cls: dataclass, mapping: dict, send_duplicate_states: bool
) -> list[dict]:
    """Convert the current state to be consumed by Afero IoT."""
    states = []
    for f in fields(cls):
        current_feature = getattr(cls, f.name, None)
        if current_feature is None:
            continue
        api_key = mapping.get(f.name, f.name)
        # There is probably a better way to approach this
        field_is_dict = str(f.type).startswith("dict")
        is_tuple_key = False
        if field_is_dict and current_feature and current_feature.keys():
            is_tuple_key = isinstance(list(current_feature.keys())[0], tuple)
        # Tuple keys signify (func_class / func_instance).
        if field_is_dict and is_tuple_key:
            states.extend(
                get_afero_states_from_mapped(
                    elem, f.name, current_feature, send_duplicate_states
                )
            )
        elif field_is_dict and not current_feature:
            continue
        else:
            # We need to determine funcClass / funcInstance when we dump our data
            if (
                current_feature == getattr(elem, f.name, None)
                and not send_duplicate_states
            ):
                continue
            current_feature_value = current_feature
            if hasattr(current_feature, "api_value"):
                current_feature_value = current_feature.api_value
            if not isinstance(current_feature_value, list):
                func_instance = get_afero_instance_for_state(
                    elem, current_feature, api_key
                )
                states.append(
                    get_afero_state_from_feature(
                        api_key, func_instance, current_feature_value
                    )
                )
            else:
                states.extend(get_afero_states_from_list(current_feature_value))
    return states


def get_afero_states_from_mapped(
    element: AferoResource,
    field_name: str,
    update_vals: dict,
    send_duplicate_states: bool,
) -> list[dict]:
    """Convert an update element to dict to be consumed by Afero API."""
    states = []
    current_elems = getattr(element, field_name, None)
    for key, val in update_vals.items():
        if val == current_elems.get(key, None) and not send_duplicate_states:
            continue
        states.append(
            {
                "functionClass": key[0],
                "functionInstance": key[1],
                "lastUpdateTime": int(time.time()),
                "value": val.api_value,
            }
        )
    return states


def get_afero_instance_for_state(
    elem: AferoResource, feature, mapped_afero_key: str | None
) -> str | None:
    """Determine the function instance based on the field data or device."""
    if hasattr(feature, "func_instance") and getattr(feature, "func_instance", None):
        instance = getattr(feature, "func_instance", None)
    elif (
        mapped_afero_key
        and hasattr(elem, "get_instance")
        and elem.get_instance(mapped_afero_key)
    ):
        instance = elem.get_instance(mapped_afero_key)
    else:
        instance = None
    return instance


def get_afero_state_from_feature(
    func_class: str, func_instance: str | None, current_val: Any
) -> dict:
    """Generate a single state from the current data."""
    new_state = {
        "functionClass": func_class,
        "functionInstance": func_instance,
        "lastUpdateTime": int(time.time()),
        "value": None,
    }
    if isinstance(current_val, dict):
        new_state.update(current_val)
    else:
        new_state["value"] = current_val
    return new_state


def get_afero_states_from_list(states: list[dict]) -> list[dict]:
    """Add timestamp to the states.

    Assume the state already has functionClass, functionState, and value
    """
    for state in states:
        state["lastUpdateTime"] = int(time.time())
    return states
