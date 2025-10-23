"""Handle connecting to Afero IoT and distribute events."""

import asyncio
from asyncio.coroutines import iscoroutinefunction
from collections.abc import Callable
import contextlib
import datetime
from enum import Enum
from types import NoneType
from typing import TYPE_CHECKING, Any, NamedTuple, NotRequired, TypedDict

from aiohttp.client_exceptions import ClientError
from aiohttp.web_exceptions import HTTPForbidden, HTTPTooManyRequests

from aioafero.device import AferoDevice, get_afero_device
from aioafero.errors import InvalidAuth
from aioafero.types import EventType
from aioafero.v1.models import ResourceTypes
from aioafero.v1.v1_const import VERSION_POLL_INTERVAL_SECONDS

if TYPE_CHECKING:  # pragma: no cover
    from aioafero.v1 import AferoBridgeV1


class BackoffException(Exception):
    """Exception raised when a backoff is required."""


class CallbackResponse(NamedTuple):
    """Callback response for DEVICE_SPLIT_CALLBACKS.

    :param split_devices: New devices that should be added to the overall list
    :param remove_original: Remove the original device from the list of devices
    """

    split_devices: list[AferoDevice] = []
    remove_original: bool = False


class EventStreamStatus(Enum):
    """Status options of EventStream."""

    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 2


class AferoEvent(TypedDict):
    """Afero IoT Event message as emitted by the EventStream."""

    type: EventType  # = EventType (add, update, delete)
    device_id: NotRequired[str]  # ID for interacting with the device
    device: NotRequired[AferoDevice]  # Afero Device
    polled_data: NotRequired[Any]  # All data polled from the API
    polled_devices: NotRequired[Any]  # All devices after the device split callbacks
    force_forward: NotRequired[bool]


EventCallBackType = Callable[[EventType, dict | None], None]
EventSubscriptionType = tuple[
    EventCallBackType,
    "tuple[EventType] | None",
    "tuple[ResourceTypes] | None",
]


class EventStream:
    """Data gatherer and eventer.

    Polls Afero IoT API, converts the response into devices, and notifies subscribers
    of the event.
    """

    def __init__(
        self, bridge: "AferoBridgeV1", polling_interval: int, poll_version: bool
    ) -> None:
        """Initialize instance."""
        self._bridge = bridge
        self._listeners = set()
        self._event_queue = asyncio.Queue()
        self._status = EventStreamStatus.DISCONNECTED
        self._scheduled_tasks: list[asyncio.Task] = []
        self._subscribers: list[EventSubscriptionType] = []
        self._logger = bridge.logger.getChild("events")
        self._polling_interval: int = polling_interval
        self._multiple_device_finder: dict[str, callable] = {}
        self._version_poll_time: datetime.datetime | None = None
        self._version_poll_enabled: bool = poll_version
        self._first_poll_completed: bool = False

    @property
    def connected(self) -> bool:
        """Return bool if we're connected."""
        return self._status == EventStreamStatus.CONNECTED

    @property
    def status(self) -> EventStreamStatus:
        """Return connection status."""
        return self._status

    @property
    def registered_multiple_devices(self) -> dict[str, Callable]:
        """Get all registered callbacks for splitting devices."""
        return self._multiple_device_finder

    @property
    def polling_interval(self) -> int:
        """Number of seconds between polling."""
        return self._polling_interval

    @polling_interval.setter
    def polling_interval(self, polling_interval: int) -> None:
        """Set the time between polling Afero API."""
        self._polling_interval = polling_interval

    @property
    def poll_version(self) -> bool:
        """Determine if version polling should occur."""
        if not self._version_poll_enabled:
            return False
        now = datetime.datetime.now(datetime.UTC)
        if self._version_poll_time is None:
            self._version_poll_time = now
            return True
        if (
            now - self._version_poll_time
        ).total_seconds() >= VERSION_POLL_INTERVAL_SECONDS:
            self._version_poll_time = now
            return True
        return False

    async def wait_for_first_poll(self) -> None:
        """Wait until the first poll has completed."""
        while not self._first_poll_completed:
            await asyncio.sleep(0.05)

    async def initialize(self) -> None:
        """Start the polling processes."""
        if len(self._scheduled_tasks) == 0:
            await self.initialize_reader()
            await self.initialize_processor()

    async def initialize_reader(self) -> None:
        """Initialize gathering data from Afero API."""
        self._scheduled_tasks.append(asyncio.create_task(self.__event_reader()))

    async def initialize_processor(self) -> None:
        """Initialize the processor."""
        self._scheduled_tasks.append(asyncio.create_task(self.__event_processor()))

    def register_multi_device(self, name: str, generate_devices: callable):
        """Register a callable to find multi-devices within the payload.

        The callable must return a list of tracked AferoDevices
        """
        self._multiple_device_finder[name] = generate_devices

    async def stop(self) -> None:
        """Stop listening for events."""
        with contextlib.suppress(asyncio.CancelledError):
            for task in self._scheduled_tasks:
                task.cancel()
            self._status = EventStreamStatus.DISCONNECTED
            self._scheduled_tasks = []

    def subscribe(
        self,
        callback: EventCallBackType,
        event_filter: EventType | tuple[EventType] | None = None,
        resource_filter: tuple[str] | None = None,
    ) -> Callable:
        """Subscribe to events emitted.

        :param callback: callback function to call when an event emits.
        :param event_filter:  Optionally provide an EventType as filter.
        :param resource_filter: Optionally provide a ResourceType as filter.

        Returns:
            function to unsubscribe.

        """
        if not isinstance(event_filter, NoneType | tuple):
            event_filter = (event_filter,)
        if not isinstance(resource_filter, NoneType | tuple):
            resource_filter = (resource_filter,)
        subscription = (callback, event_filter, resource_filter)

        def unsubscribe():
            self._subscribers.remove(subscription)

        self._subscribers.append(subscription)
        return unsubscribe

    def add_job(self, event: AferoEvent) -> None:
        """Manually add a job to be processed."""
        self._event_queue.put_nowait(event)

    async def async_block_until_done(self):
        """Blocking call until everything has finished."""
        attempt = 0
        while not self._event_queue.empty():
            self._logger.debug(
                "Number of events in queue: %d", self._event_queue.qsize()
            )
            await asyncio.sleep(0.01)
            attempt += 1
            if attempt > 100:
                self._logger.warning(
                    "Queue did not empty within a second. Breaking out of the wait"
                )
                break

    def emit(self, event_type: EventType, data: AferoEvent = None) -> None:
        """Emit event to all listeners."""
        for callback, event_filter, resource_filter in self._subscribers:
            try:
                if event_filter is not None and event_type not in event_filter:
                    continue
                if (
                    resource_filter is not None
                    and data is not None
                    and (
                        "device" in data
                        and data["device"]
                        and not any(
                            data["device"].device_class == res_filter
                            for res_filter in resource_filter
                        )
                    )
                ):
                    continue
                if iscoroutinefunction(callback):
                    self._bridge.add_job(
                        asyncio.create_task(callback(event_type, data))
                    )
                else:
                    callback(event_type, data)
            except Exception:
                self._logger.exception("Unhandled exception. Please open a bug report")

    async def process_backoff(self, attempt: int) -> None:
        """Handle backoff timer for Afero IoT API.

        :param attempt: Number of attempts
        :param reason: Reason why the backoff is occurring
        """
        backoff_time = min(attempt * self.polling_interval, 600)
        debug_message = f"Waiting {backoff_time} seconds before next poll"
        if attempt == 1:
            self._logger.info("Lost connection to the Afero IoT API.")
            self._logger.debug(debug_message)
        if self._status != EventStreamStatus.DISCONNECTED:
            self._status = EventStreamStatus.DISCONNECTED
            self.emit(EventType.DISCONNECTED)
        await asyncio.sleep(backoff_time)

    async def gather_data(self) -> list[dict[Any, str]]:
        """Gather all data from the Afero IoT API."""
        consecutive_http_errors = 0
        while True:
            try:
                data = await self._bridge.fetch_data(version_poll=self.poll_version)
            except TimeoutError:
                self._logger.warning("Timeout when contacting Afero IoT API.")
                await self.process_backoff(consecutive_http_errors)
            except InvalidAuth:
                consecutive_http_errors += 1
                self._logger.warning("Invalid credentials provided.")
                await self.process_backoff(consecutive_http_errors)
            except (HTTPForbidden, HTTPTooManyRequests, ClientError):
                consecutive_http_errors += 1
                await self.process_backoff(consecutive_http_errors)
            except TypeError as err:
                self._logger.warning(
                    "Unexpected data from Afero IoT API, %s.", err.args[0]
                )
                consecutive_http_errors += 1
                await self.process_backoff(consecutive_http_errors)
            except Exception:
                self._logger.exception(
                    "Unknown error occurred. Please open a bug report."
                )
                raise
            else:
                # Successful connection
                if consecutive_http_errors > 0:
                    self._logger.info("Reconnected to the Afero IoT API")
                    self.emit(EventType.RECONNECTED)
                elif self._status != EventStreamStatus.CONNECTED:
                    self._status = EventStreamStatus.CONNECTED
                    self.emit(EventType.CONNECTED)
                return data

    async def generate_devices_from_data(
        self, data: list[dict[Any, str]]
    ) -> list[AferoDevice]:
        """Generate all devices from a given payload.

        Generating devices will attempt to split devices where required and remove
        devices that are no longer needed, as identified by the callback.
        """
        devices = [
            get_afero_device(dev)
            for dev in data
            if dev.get("typeId") == ResourceTypes.DEVICE.value
            and dev.get("description", {}).get("device", {}).get("deviceClass")
        ]
        for device in devices:
            self._bridge.add_afero_dev(device)
        return await self.split_devices(devices)

    async def split_devices(self, devices: list[AferoDevice]) -> list[AferoDevice]:
        """Split Afero devices into multiple devices where required."""
        for name, multi_dev_callable in self._multiple_device_finder.items():
            for dev in devices[:]:
                multi_devs, remove_root = multi_dev_callable(dev)
                if remove_root:
                    with contextlib.suppress(KeyError):
                        devices.remove(dev)
                if multi_devs:
                    self._logger.debug(
                        "Found %s devices from %s", len(multi_devs), name
                    )
                    for split_dev in multi_devs:
                        self._bridge.add_afero_dev(dev, split_dev.id)
                        dev.children.append(split_dev.id)
                    devices.extend(multi_devs)
        self._logger.debug("Total number of devices (post split): %s", len(devices))
        return devices

    async def generate_events_from_update(self, dev: AferoDevice) -> None:
        """Generate updates for a single device update."""
        devices = await self.split_devices([dev])
        self._logger.debug(
            "Received update for device %s. Generating %d events",
            dev.device_class,
            len(devices),
        )
        for device in devices:
            self._event_queue.put_nowait(
                AferoEvent(
                    type=EventType.RESOURCE_UPDATE_RESPONSE,
                    device_id=device.id,
                    device=device,
                    force_forward=False,
                )
            )

    async def generate_events_from_data(self, data: list[dict[Any, str]]) -> None:
        """Process the raw Afero IoT data for emitting.

        :param data: Raw data from Afero IoT
        """
        processed_ids = []
        skipped_ids = []
        devices = await self.generate_devices_from_data(data)
        self._event_queue.put_nowait(
            AferoEvent(
                type=EventType.POLLED_DATA,
                polled_data=data,
                force_forward=False,
            )
        )
        self._event_queue.put_nowait(
            AferoEvent(
                type=EventType.POLLED_DEVICES,
                polled_devices=devices,
                force_forward=False,
            )
        )
        for device in devices:
            event_type = EventType.RESOURCE_UPDATED
            if device.id not in self._bridge.tracked_devices:
                event_type = EventType.RESOURCE_ADDED
            self._event_queue.put_nowait(
                AferoEvent(
                    type=event_type,
                    device_id=device.id,
                    device=device,
                    force_forward=False,
                )
            )
            processed_ids.append(device.id)
        # Handle devices that did not report in from the API
        for dev_id in self._bridge.tracked_devices:
            if dev_id not in processed_ids + skipped_ids:
                self._event_queue.put_nowait(
                    AferoEvent(type=EventType.RESOURCE_DELETED, device_id=dev_id)
                )
                self._bridge.remove_device(dev_id)

    async def perform_poll(self) -> None:
        """Poll Afero IoT and generate the required events."""
        try:
            data = await self.gather_data()
        except Exception:  # noqa: BLE001
            self._status = EventStreamStatus.DISCONNECTED
            self.emit(EventType.DISCONNECTED)
        else:
            try:
                await self.generate_events_from_data(data)
            except Exception:
                self._logger.exception("Unable to process Afero IoT data. %s", data)
            self._first_poll_completed = True

    async def __event_reader(self) -> None:
        """Poll the current states."""
        self._status = EventStreamStatus.CONNECTING
        while True:
            await self.perform_poll()
            await asyncio.sleep(self._polling_interval)

    async def process_event(self):
        """Process a single event in the queue."""
        try:
            event: AferoEvent = await self._event_queue.get()
            self.emit(event["type"], event)
        except Exception:
            self._logger.exception("Unhandled exception. Please open a bug report")

    async def __event_processor(self) -> None:
        """Process the Afero IoT devices."""
        while True:
            await self.process_event()
