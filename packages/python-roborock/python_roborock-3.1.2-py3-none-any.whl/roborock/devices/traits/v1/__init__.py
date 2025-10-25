"""Create traits for V1 devices.

Traits are modular components that encapsulate specific features of a Roborock
device. This module provides a factory function to create and initialize the
appropriate traits for V1 devices based on their capabilities. They can also
be considered groups of commands and parsing logic for that command.

Traits have a `refresh()` method that can be called to update their state
from the device. Some traits may also provide additional methods for modifying
the device state.

The most common pattern for a trait is to subclass `V1TraitMixin` and a `RoborockBase`
dataclass, and define a `command` class variable that specifies the `RoborockCommand`
used to fetch the trait data from the device. See `common.py` for more details
on common patterns used across traits.

There are some additional decorators in `common.py` that can be used to specify which
RPC channel to use for the trait (standard, MQTT/cloud, or map-specific).

  - `@common.mqtt_rpc_channel` - Use the MQTT RPC channel for this trait.
  - `@common.map_rpc_channel` - Use the map RPC channel for this trait.

There are also some attributes that specify device feature dependencies for
optional traits:

    - `requires_feature` - The string name of the device feature that must be supported
        for this trait to be enabled. See `DeviceFeaturesTrait` for a list of
        available features.
    - `requires_dock_type` - If set, this is a function that accepts a `RoborockDockTypeCode`
        and returns a boolean indicating whether the trait is supported for that dock type.
"""

import logging
from dataclasses import dataclass, field, fields
from typing import Any, get_args

from roborock.data.containers import HomeData, HomeDataProduct
from roborock.data.v1.v1_code_mappings import RoborockDockTypeCode
from roborock.devices.cache import Cache
from roborock.devices.traits import Trait
from roborock.devices.v1_rpc_channel import V1RpcChannel
from roborock.map.map_parser import MapParserConfig

from .child_lock import ChildLockTrait
from .clean_summary import CleanSummaryTrait
from .command import CommandTrait
from .common import V1TraitMixin
from .consumeable import ConsumableTrait
from .device_features import DeviceFeaturesTrait
from .do_not_disturb import DoNotDisturbTrait
from .dust_collection_mode import DustCollectionModeTrait
from .flow_led_status import FlowLedStatusTrait
from .home import HomeTrait
from .led_status import LedStatusTrait
from .map_content import MapContentTrait
from .maps import MapsTrait
from .network_info import NetworkInfoTrait
from .rooms import RoomsTrait
from .smart_wash_params import SmartWashParamsTrait
from .status import StatusTrait
from .valley_electricity_timer import ValleyElectricityTimerTrait
from .volume import SoundVolumeTrait
from .wash_towel_mode import WashTowelModeTrait

_LOGGER = logging.getLogger(__name__)

__all__ = [
    "create",
    "PropertiesApi",
    "StatusTrait",
    "DoNotDisturbTrait",
    "CleanSummaryTrait",
    "SoundVolumeTrait",
    "MapsTrait",
    "MapContentTrait",
    "ConsumableTrait",
    "HomeTrait",
    "DeviceFeaturesTrait",
    "CommandTrait",
    "ChildLockTrait",
    "FlowLedStatusTrait",
    "LedStatusTrait",
    "ValleyElectricityTimerTrait",
    "DustCollectionModeTrait",
    "WashTowelModeTrait",
    "SmartWashParamsTrait",
    "NetworkInfoTrait",
]


@dataclass
class PropertiesApi(Trait):
    """Common properties for V1 devices.

    This class holds all the traits that are common across all V1 devices.
    """

    # All v1 devices have these traits
    status: StatusTrait
    command: CommandTrait
    dnd: DoNotDisturbTrait
    clean_summary: CleanSummaryTrait
    sound_volume: SoundVolumeTrait
    rooms: RoomsTrait
    maps: MapsTrait
    map_content: MapContentTrait
    consumables: ConsumableTrait
    home: HomeTrait
    device_features: DeviceFeaturesTrait
    network_info: NetworkInfoTrait

    # Optional features that may not be supported on all devices
    child_lock: ChildLockTrait | None = None
    led_status: LedStatusTrait | None = None
    flow_led_status: FlowLedStatusTrait | None = None
    valley_electricity_timer: ValleyElectricityTimerTrait | None = None
    dust_collection_mode: DustCollectionModeTrait | None = None
    wash_towel_mode: WashTowelModeTrait | None = None
    smart_wash_params: SmartWashParamsTrait | None = None

    def __init__(
        self,
        device_uid: str,
        product: HomeDataProduct,
        home_data: HomeData,
        rpc_channel: V1RpcChannel,
        mqtt_rpc_channel: V1RpcChannel,
        map_rpc_channel: V1RpcChannel,
        cache: Cache,
        map_parser_config: MapParserConfig | None = None,
    ) -> None:
        """Initialize the V1TraitProps."""
        self._device_uid = device_uid
        self._rpc_channel = rpc_channel
        self._mqtt_rpc_channel = mqtt_rpc_channel
        self._map_rpc_channel = map_rpc_channel
        self._cache = cache

        self.status = StatusTrait(product)
        self.consumables = ConsumableTrait()
        self.rooms = RoomsTrait(home_data)
        self.maps = MapsTrait(self.status)
        self.map_content = MapContentTrait(map_parser_config)
        self.home = HomeTrait(self.status, self.maps, self.rooms, cache)
        self.device_features = DeviceFeaturesTrait(product.product_nickname, cache)
        self.network_info = NetworkInfoTrait(device_uid, cache)

        # Dynamically create any traits that need to be populated
        for item in fields(self):
            if (trait := getattr(self, item.name, None)) is None:
                # We exclude optional features and them via discover_features
                if (union_args := get_args(item.type)) is None or len(union_args) > 0:
                    continue
                _LOGGER.debug("Trait '%s' is supported, initializing", item.name)
                trait = item.type()
                setattr(self, item.name, trait)
            # This is a hack to allow setting the rpc_channel on all traits. This is
            # used so we can preserve the dataclass behavior when the values in the
            # traits are updated, but still want to allow them to have a reference
            # to the rpc channel for sending commands.
            trait._rpc_channel = self._get_rpc_channel(trait)

    def _get_rpc_channel(self, trait: V1TraitMixin) -> V1RpcChannel:
        # The decorator `@common.mqtt_rpc_channel` means that the trait needs
        # to use the mqtt_rpc_channel (cloud only) instead of the rpc_channel (adaptive)
        if hasattr(trait, "mqtt_rpc_channel"):
            return self._mqtt_rpc_channel
        elif hasattr(trait, "map_rpc_channel"):
            return self._map_rpc_channel
        else:
            return self._rpc_channel

    async def discover_features(self) -> None:
        """Populate any supported traits that were not initialized in __init__."""
        _LOGGER.debug("Starting optional trait discovery")
        await self.device_features.refresh()
        # Dock type also acts like a device feature for some traits.
        dock_type = await self._dock_type()

        # Dynamically create any traits that need to be populated
        for item in fields(self):
            if (trait := getattr(self, item.name, None)) is not None:
                continue
            if (union_args := get_args(item.type)) is None:
                raise ValueError(f"Unexpected non-union type for trait {item.name}: {item.type}")
            if len(union_args) != 2 or type(None) not in union_args:
                raise ValueError(f"Unexpected non-optional type for trait {item.name}: {item.type}")

            # Union args may not be in declared order
            item_type = union_args[0] if union_args[1] is type(None) else union_args[1]
            if not self._is_supported(item_type, item.name, dock_type):
                _LOGGER.debug("Trait '%s' not supported, skipping", item.name)
                continue
            _LOGGER.debug("Trait '%s' is supported, initializing", item.name)
            trait = item_type()
            setattr(self, item.name, trait)
            trait._rpc_channel = self._get_rpc_channel(trait)

    def _is_supported(self, trait_type: type[V1TraitMixin], name: str, dock_type: RoborockDockTypeCode) -> bool:
        """Check if a trait is supported by the device."""

        if (requires_dock_type := getattr(trait_type, "requires_dock_type", None)) is not None:
            return requires_dock_type(dock_type)

        if (feature_name := getattr(trait_type, "requires_feature", None)) is None:
            _LOGGER.debug("Optional trait missing 'requires_feature' attribute %s, skipping", name)
            return False
        if (is_supported := getattr(self.device_features, feature_name)) is None:
            raise ValueError(f"Device feature '{feature_name}' on trait '{name}' is unknown")
        return is_supported

    async def _dock_type(self) -> RoborockDockTypeCode:
        """Get the dock type from the status trait or cache."""
        dock_type = await self._get_cached_trait_data("dock_type")
        if dock_type is not None:
            _LOGGER.debug("Using cached dock type: %s", dock_type)
            try:
                return RoborockDockTypeCode(dock_type)
            except ValueError:
                _LOGGER.debug("Cached dock type %s is invalid, refreshing", dock_type)

        _LOGGER.debug("Starting dock type discovery")
        await self.status.refresh()
        _LOGGER.debug("Fetched dock type: %s", self.status.dock_type)
        if self.status.dock_type is None:
            # Explicitly set so we reuse cached value next type
            dock_type = RoborockDockTypeCode.no_dock
        else:
            dock_type = self.status.dock_type
        await self._set_cached_trait_data("dock_type", dock_type)
        return dock_type

    async def _get_cached_trait_data(self, name: str) -> Any:
        """Get the dock type from the status trait or cache."""
        cache_data = await self._cache.get()
        if cache_data.trait_data is None:
            cache_data.trait_data = {}
        _LOGGER.debug("Cached trait data: %s", cache_data.trait_data)
        return cache_data.trait_data.get(name)

    async def _set_cached_trait_data(self, name: str, value: Any) -> None:
        """Set trait-specific cached data."""
        cache_data = await self._cache.get()
        if cache_data.trait_data is None:
            cache_data.trait_data = {}
        cache_data.trait_data[name] = value
        _LOGGER.debug("Updating cached trait data: %s", cache_data.trait_data)
        await self._cache.set(cache_data)


def create(
    device_uid: str,
    product: HomeDataProduct,
    home_data: HomeData,
    rpc_channel: V1RpcChannel,
    mqtt_rpc_channel: V1RpcChannel,
    map_rpc_channel: V1RpcChannel,
    cache: Cache,
    map_parser_config: MapParserConfig | None = None,
) -> PropertiesApi:
    """Create traits for V1 devices."""
    return PropertiesApi(
        device_uid,
        product,
        home_data,
        rpc_channel,
        mqtt_rpc_channel,
        map_rpc_channel,
        cache,
        map_parser_config,
    )
