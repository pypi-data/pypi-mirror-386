"""Controller holding and managing Afero IoT resources of type `lock`."""

from aioafero.device import AferoDevice
from aioafero.v1.models import features
from aioafero.v1.models.lock import Lock, LockPut
from aioafero.v1.models.resource import DeviceInformation, ResourceTypes

from .base import AferoBinarySensor, AferoSensor, BaseResourcesController


class LockController(BaseResourcesController[Lock]):
    """Controller holding and managing Afero IoT resources of type `lock`."""

    ITEM_TYPE_ID = ResourceTypes.DEVICE
    ITEM_TYPES = [ResourceTypes.LOCK]
    ITEM_CLS = Lock
    ITEM_MAPPING = {"position": "lock-control"}

    async def lock(self, device_id: str) -> None:
        """Engage the lock."""
        await self.set_state(
            device_id, lock_position=features.CurrentPositionEnum.LOCKING
        )

    async def unlock(self, device_id: str) -> None:
        """Disengage the lock."""
        await self.set_state(
            device_id, lock_position=features.CurrentPositionEnum.UNLOCKING
        )

    async def initialize_elem(self, afero_device: AferoDevice) -> Lock:
        """Initialize the element.

        :param afero_device: Afero Device that contains the updated states

        :return: Newly initialized resource
        """
        available: bool = False
        current_position: features.CurrentPositionFeature | None = None
        sensors: dict[str, AferoSensor] = {}
        binary_sensors: dict[str, AferoBinarySensor] = {}
        for state in afero_device.states:
            if state.functionClass == "lock-control":
                current_position = features.CurrentPositionFeature(
                    position=features.CurrentPositionEnum(state.value)
                )
            elif state.functionClass == "available":
                available = state.value

        self._items[afero_device.id] = Lock(
            _id=afero_device.id,
            available=available,
            sensors=sensors,
            binary_sensors=binary_sensors,
            device_information=DeviceInformation(
                device_class=afero_device.device_class,
                default_image=afero_device.default_image,
                default_name=afero_device.default_name,
                manufacturer=afero_device.manufacturerName,
                model=afero_device.model,
                name=afero_device.friendly_name,
                parent_id=afero_device.device_id,
                children=afero_device.children,
                functions=afero_device.functions,
            ),
            position=current_position,
        )
        return self._items[afero_device.id]

    async def update_elem(self, afero_device: AferoDevice) -> set:
        """Update the Lock with the latest API data.

        :param afero_device: Afero Device that contains the updated states

        :return: States that have been modified
        """
        cur_item = self.get_device(afero_device.id)
        updated_keys = set()
        for state in afero_device.states:
            if state.functionClass == "lock-control":
                new_val = features.CurrentPositionEnum(state.value)
                if cur_item.position.position != new_val:
                    updated_keys.add("position")
                cur_item.position.position = features.CurrentPositionEnum(state.value)
            elif state.functionClass == "available":
                if cur_item.available != state.value:
                    updated_keys.add("available")
                cur_item.available = state.value

        return updated_keys

    async def set_state(
        self,
        device_id: str,
        lock_position: features.CurrentPositionEnum | None = None,
    ) -> None:
        """Set supported feature(s) to lock resource."""
        update_obj = LockPut()
        if lock_position is not None:
            update_obj.position = features.CurrentPositionFeature(
                position=lock_position
            )
        await self.update(device_id, obj_in=update_obj)
