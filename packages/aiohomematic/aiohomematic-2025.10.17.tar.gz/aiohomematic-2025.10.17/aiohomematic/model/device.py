# SPDX-License-Identifier: MIT
# Copyright (c) 2021-2025
"""
Device and channel model for AioHomematic.

This module implements the runtime representation of a Homematic device and its
channels, including creation and lookup of data points/events, firmware and
availability handling, link management, value caching, and exporting of device
definitions for diagnostics.

Key classes:
- Device: Encapsulates metadata, channels, and operations for a single device.
- Channel: Represents a functional channel with its data points and events.

Other components:
- _ValueCache: Lazy loading and caching of parameter values to minimize RPCs.
- _DefinitionExporter: Utility to export device and paramset descriptions.

The Device/Channel classes are the anchor used by generic, custom, calculated,
 and hub model code to attach data points and events.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from datetime import datetime
from functools import partial
import logging
import os
import random
from typing import Any, Final

import orjson

from aiohomematic import central as hmcu, client as hmcl
from aiohomematic.async_support import loop_check
from aiohomematic.const import (
    ADDRESS_SEPARATOR,
    CALLBACK_TYPE,
    CLICK_EVENTS,
    DEVICE_DESCRIPTIONS_DIR,
    IDENTIFIER_SEPARATOR,
    INIT_DATETIME,
    NO_CACHE_ENTRY,
    PARAMSET_DESCRIPTIONS_DIR,
    RELEVANT_INIT_PARAMETERS,
    REPORT_VALUE_USAGE_DATA,
    REPORT_VALUE_USAGE_VALUE_ID,
    VIRTUAL_REMOTE_MODELS,
    CallSource,
    DataOperationResult,
    DataPointCategory,
    DataPointKey,
    DataPointUsage,
    DeviceDescription,
    DeviceFirmwareState,
    EventType,
    ForcedDeviceAvailability,
    Interface,
    Manufacturer,
    Parameter,
    ParameterData,
    ParamsetKey,
    ProductGroup,
    RxMode,
    check_ignore_model_on_initial_load,
)
from aiohomematic.decorators import inspector
from aiohomematic.exceptions import AioHomematicException, BaseHomematicException
from aiohomematic.model.calculated import CalculatedDataPoint
from aiohomematic.model.custom import data_point as hmce, definition as hmed
from aiohomematic.model.data_point import BaseParameterDataPoint, CallbackDataPoint
from aiohomematic.model.event import GenericEvent
from aiohomematic.model.generic import GenericDataPoint
from aiohomematic.model.support import (
    ChannelNameData,
    generate_channel_unique_id,
    get_channel_name_data,
    get_device_name,
)
from aiohomematic.model.update import DpUpdate
from aiohomematic.property_decorators import hm_property, info_property, state_property
from aiohomematic.support import (
    CacheEntry,
    LogContextMixin,
    PayloadMixin,
    check_or_create_directory,
    extract_exc_args,
    get_channel_address,
    get_channel_no,
    get_rx_modes,
)

__all__ = ["Channel", "Device"]

_LOGGER: Final = logging.getLogger(__name__)


class Device(LogContextMixin, PayloadMixin):
    """Object to hold information about a device and associated data points."""

    __slots__ = (
        "_address",
        "_cached_relevant_for_central_link_management",
        "_central",
        "_channel_group",
        "_channels",
        "_client",
        "_description",
        "_device_updated_callbacks",
        "_firmware_update_callbacks",
        "_forced_availability",
        "_group_channels",
        "_has_custom_data_point_definition",
        "_id",
        "_ignore_for_custom_data_point",
        "_ignore_on_initial_load",
        "_interface",
        "_interface_id",
        "_is_updatable",
        "_manufacturer",
        "_model",
        "_modified_at",
        "_name",
        "_product_group",
        "_rooms",
        "_rx_modes",
        "_sub_model",
        "_update_data_point",
        "_value_cache",
    )

    def __init__(self, *, central: hmcu.CentralUnit, interface_id: str, device_address: str) -> None:
        """Initialize the device object."""
        PayloadMixin.__init__(self)
        self._central: Final = central
        self._interface_id: Final = interface_id
        self._address: Final = device_address
        self._channel_group: Final[dict[int | None, int]] = {}
        self._group_channels: Final[dict[int, set[int | None]]] = {}
        self._id: Final = self._central.device_details.get_address_id(address=device_address)
        self._interface: Final = central.device_details.get_interface(address=device_address)
        self._client: Final = central.get_client(interface_id=interface_id)
        self._description = self._central.device_descriptions.get_device_description(
            interface_id=interface_id, address=device_address
        )
        _LOGGER.debug(
            "__INIT__: Initializing device: %s, %s",
            interface_id,
            device_address,
        )

        self._modified_at: datetime = INIT_DATETIME
        self._forced_availability: ForcedDeviceAvailability = ForcedDeviceAvailability.NOT_SET
        self._device_updated_callbacks: Final[list[Callable]] = []
        self._firmware_update_callbacks: Final[list[Callable]] = []
        self._model: Final[str] = self._description["TYPE"]
        self._ignore_on_initial_load: Final[bool] = check_ignore_model_on_initial_load(model=self._model)
        self._is_updatable: Final = self._description.get("UPDATABLE") or False
        self._rx_modes: Final = get_rx_modes(mode=self._description.get("RX_MODE", 0))
        self._sub_model: Final[str | None] = self._description.get("SUBTYPE")
        self._ignore_for_custom_data_point: Final[bool] = central.parameter_visibility.model_is_ignored(
            model=self._model
        )
        self._manufacturer = self._identify_manufacturer()
        self._product_group: Final = self._client.get_product_group(model=self._model)
        # marker if device will be created as custom data_point
        self._has_custom_data_point_definition: Final = (
            hmed.data_point_definition_exists(model=self._model) and not self._ignore_for_custom_data_point
        )
        self._name: Final = get_device_name(
            central=central,
            device_address=device_address,
            model=self._model,
        )
        channel_addresses = tuple(
            [device_address] + [address for address in self._description["CHILDREN"] if address != ""]
        )
        self._channels: Final[dict[str, Channel]] = {
            address: Channel(device=self, channel_address=address) for address in channel_addresses
        }
        self._value_cache: Final[_ValueCache] = _ValueCache(device=self)
        self._rooms: Final = central.device_details.get_device_rooms(device_address=device_address)
        self._update_data_point: Final = DpUpdate(device=self) if self.is_updatable else None
        _LOGGER.debug(
            "__INIT__: Initialized device: %s, %s, %s, %s",
            self._interface_id,
            self._address,
            self._model,
            self._name,
        )

    def _identify_manufacturer(self) -> Manufacturer:
        """Identify the manufacturer of a device."""
        if self._model.lower().startswith("hb"):
            return Manufacturer.HB
        if self._model.lower().startswith("alpha"):
            return Manufacturer.MOEHLENHOFF
        return Manufacturer.EQ3

    @info_property(log_context=True)
    def address(self) -> str:
        """Return the address of the device."""
        return self._address

    @property
    def allow_undefined_generic_data_points(self) -> bool:
        """Return if undefined generic data points of this device are allowed."""
        return bool(
            all(
                channel.custom_data_point.allow_undefined_generic_data_points
                for channel in self._channels.values()
                if channel.custom_data_point is not None
            )
        )

    @state_property
    def available(self) -> bool:
        """Return the availability of the device."""
        if self._forced_availability != ForcedDeviceAvailability.NOT_SET:
            return self._forced_availability == ForcedDeviceAvailability.FORCE_TRUE
        if (un_reach := self._dp_un_reach) is None:
            un_reach = self._dp_sticky_un_reach
        if un_reach is not None and un_reach.value is not None:
            return not un_reach.value
        return True

    @property
    def available_firmware(self) -> str | None:
        """Return the available firmware of the device."""
        return str(self._description.get("AVAILABLE_FIRMWARE", ""))

    @property
    def calculated_data_points(self) -> tuple[CalculatedDataPoint, ...]:
        """Return the generic data points."""
        data_points: list[CalculatedDataPoint] = []
        for channel in self._channels.values():
            data_points.extend(channel.calculated_data_points)
        return tuple(data_points)

    @property
    def central(self) -> hmcu.CentralUnit:
        """Return the central of the device."""
        return self._central

    @property
    def channels(self) -> Mapping[str, Channel]:
        """Return the channels."""
        return self._channels

    @property
    def client(self) -> hmcl.Client:
        """Return the client of the device."""
        return self._client

    @property
    def config_pending(self) -> bool:
        """Return if a config change of the device is pending."""
        if self._dp_config_pending is not None and self._dp_config_pending.value is not None:
            return self._dp_config_pending.value is True
        return False

    @property
    def custom_data_points(self) -> tuple[hmce.CustomDataPoint, ...]:
        """Return the custom data points."""
        return tuple(
            channel.custom_data_point for channel in self._channels.values() if channel.custom_data_point is not None
        )

    @info_property
    def firmware(self) -> str:
        """Return the firmware of the device."""
        return self._description.get("FIRMWARE") or "0.0"

    @property
    def firmware_updatable(self) -> bool:
        """Return the firmware update state of the device."""
        return self._description.get("FIRMWARE_UPDATABLE") or False

    @property
    def firmware_update_state(self) -> DeviceFirmwareState:
        """Return the firmware update state of the device."""
        return DeviceFirmwareState(self._description.get("FIRMWARE_UPDATE_STATE") or DeviceFirmwareState.UNKNOWN)

    @property
    def generic_events(self) -> tuple[GenericEvent, ...]:
        """Return the generic events."""
        events: list[GenericEvent] = []
        for channel in self._channels.values():
            events.extend(channel.generic_events)
        return tuple(events)

    @property
    def generic_data_points(self) -> tuple[GenericDataPoint, ...]:
        """Return the generic data points."""
        data_points: list[GenericDataPoint] = []
        for channel in self._channels.values():
            data_points.extend(channel.generic_data_points)
        return tuple(data_points)

    @property
    def has_custom_data_point_definition(self) -> bool:
        """Return if custom_data_point definition is available for the device."""
        return self._has_custom_data_point_definition

    @property
    def has_sub_devices(self) -> bool:
        """Return if device has multiple sub device channels."""
        # If there is only one channel group, no sub devices are needed
        if len(self._group_channels) <= 1:
            return False
        count = 0
        # If there are multiple channel groups with more than one channel, there are sub devices
        for gcs in self._group_channels.values():
            if len(gcs) > 1:
                count += 1
            if count > 1:
                return True

        return False

    @property
    def id(self) -> str:
        """Return the id of the device."""
        return self._id

    @info_property
    def identifier(self) -> str:
        """Return the identifier of the device."""
        return f"{self._address}{IDENTIFIER_SEPARATOR}{self._interface_id}"

    @property
    def ignore_on_initial_load(self) -> bool:
        """Return if model should be ignored on initial load."""
        return self._ignore_on_initial_load

    @property
    def interface(self) -> Interface:
        """Return the interface of the device."""
        return self._interface

    @hm_property(log_context=True)
    def interface_id(self) -> str:
        """Return the interface_id of the device."""
        return self._interface_id

    @property
    def ignore_for_custom_data_point(self) -> bool:
        """Return if device should be ignored for custom data_point."""
        return self._ignore_for_custom_data_point

    @property
    def info(self) -> Mapping[str, Any]:
        """Return the device info."""
        device_info = dict(self.info_payload)
        device_info["central"] = self._central.info_payload
        return device_info

    @property
    def is_updatable(self) -> bool:
        """Return if the device is updatable."""
        return self._is_updatable

    @info_property
    def manufacturer(self) -> str:
        """Return the manufacturer of the device."""
        return self._manufacturer

    @info_property(log_context=True)
    def model(self) -> str:
        """Return the model of the device."""
        return self._model

    @info_property
    def name(self) -> str:
        """Return the name of the device."""
        return self._name

    @property
    def product_group(self) -> ProductGroup:
        """Return the product group of the device."""
        return self._product_group

    @info_property
    def room(self) -> str | None:
        """Return the room of the device, if only one assigned in the backend."""
        if self._rooms and len(self._rooms) == 1:
            return list(self._rooms)[0]
        if (maintenance_channel := self.get_channel(channel_address=f"{self._address}:0")) is not None:
            return maintenance_channel.room
        return None

    @property
    def rooms(self) -> set[str]:
        """Return all rooms of the device."""
        return self._rooms

    @property
    def rx_modes(self) -> tuple[RxMode, ...]:
        """Return the rx mode."""
        return self._rx_modes

    @property
    def sub_model(self) -> str | None:
        """Return the sub model of the device."""
        return self._sub_model

    @property
    def update_data_point(self) -> DpUpdate | None:
        """Return the device firmware update data_point of the device."""
        return self._update_data_point

    @property
    def value_cache(self) -> _ValueCache:
        """Return the value_cache of the device."""
        return self._value_cache

    @property
    def _dp_un_reach(self) -> GenericDataPoint | None:
        """Return th UN REACH data_point."""
        return self.get_generic_data_point(channel_address=f"{self._address}:0", parameter=Parameter.UN_REACH)

    @property
    def _dp_sticky_un_reach(self) -> GenericDataPoint | None:
        """Return th STICKY_UN_REACH data_point."""
        return self.get_generic_data_point(channel_address=f"{self._address}:0", parameter=Parameter.STICKY_UN_REACH)

    @property
    def _dp_config_pending(self) -> GenericDataPoint | None:
        """Return th CONFIG_PENDING data_point."""
        return self.get_generic_data_point(channel_address=f"{self._address}:0", parameter=Parameter.CONFIG_PENDING)

    def add_channel_to_group(self, *, group_no: int, channel_no: int | None) -> None:
        """Add channel to group."""
        if group_no not in self._group_channels:
            self._group_channels[group_no] = set()
        self._group_channels[group_no].add(channel_no)

        if group_no not in self._channel_group:
            self._channel_group[group_no] = group_no
        if channel_no not in self._channel_group:
            self._channel_group[channel_no] = group_no

    @inspector
    async def create_central_links(self) -> None:
        """Create a central links to support press events on all channels with click events."""
        if self.relevant_for_central_link_management:  # pylint: disable=using-constant-test
            for channel in self._channels.values():
                await channel.create_central_link()

    @inspector
    async def remove_central_links(self) -> None:
        """Remove central links."""
        if self.relevant_for_central_link_management:  # pylint: disable=using-constant-test
            for channel in self._channels.values():
                await channel.remove_central_link()

    @hm_property(cached=True)
    def relevant_for_central_link_management(self) -> bool:
        """Return if channel is relevant for central link management."""
        return (
            self._interface in (Interface.BIDCOS_RF, Interface.BIDCOS_WIRED, Interface.HMIP_RF)
            and self._model not in VIRTUAL_REMOTE_MODELS
        )

    def get_channel_group_no(self, *, channel_no: int | None) -> int | None:
        """Return the group no of the channel."""
        return self._channel_group.get(channel_no)

    def is_in_multi_channel_group(self, *, channel_no: int | None) -> bool:
        """Return if multiple channels are in the group."""
        if channel_no is None:
            return False

        return len([s for s, m in self._channel_group.items() if m == self._channel_group.get(channel_no)]) > 1

    def get_channel(self, *, channel_address: str) -> Channel | None:
        """Get channel of device."""
        return self._channels.get(channel_address)

    def identify_channel(self, *, text: str) -> Channel | None:
        """Identify channel within a text."""
        for channel_address, channel in self._channels.items():
            if text.endswith(channel_address):
                return channel
            if channel.id in text:
                return channel
            if channel.device.id in text:
                return channel

        return None

    def remove(self) -> None:
        """Remove data points from collections and central."""
        for channel in self._channels.values():
            channel.remove()

    def register_device_updated_callback(self, *, cb: Callable) -> CALLBACK_TYPE:
        """Register update callback."""
        if callable(cb) and cb not in self._device_updated_callbacks:
            self._device_updated_callbacks.append(cb)
            return partial(self.unregister_device_updated_callback, cb=cb)
        return None

    def unregister_device_updated_callback(self, *, cb: Callable) -> None:
        """Remove update callback."""
        if cb in self._device_updated_callbacks:
            self._device_updated_callbacks.remove(cb)

    def register_firmware_update_callback(self, *, cb: Callable) -> CALLBACK_TYPE:
        """Register firmware update callback."""
        if callable(cb) and cb not in self._firmware_update_callbacks:
            self._firmware_update_callbacks.append(cb)
            return partial(self.unregister_firmware_update_callback, cb=cb)
        return None

    def unregister_firmware_update_callback(self, *, cb: Callable) -> None:
        """Remove firmware update callback."""
        if cb in self._firmware_update_callbacks:
            self._firmware_update_callbacks.remove(cb)

    def _set_modified_at(self) -> None:
        self._modified_at = datetime.now()

    def get_data_points(
        self,
        *,
        category: DataPointCategory | None = None,
        exclude_no_create: bool = True,
        registered: bool | None = None,
    ) -> tuple[CallbackDataPoint, ...]:
        """Get all data points of the device."""
        all_data_points: list[CallbackDataPoint] = []
        if (
            self._update_data_point
            and (category is None or self._update_data_point.category == category)
            and (
                (exclude_no_create and self._update_data_point.usage != DataPointUsage.NO_CREATE)
                or exclude_no_create is False
            )
            and (registered is None or self._update_data_point.is_registered == registered)
        ):
            all_data_points.append(self._update_data_point)
        for channel in self._channels.values():
            all_data_points.extend(
                channel.get_data_points(category=category, exclude_no_create=exclude_no_create, registered=registered)
            )
        return tuple(all_data_points)

    def get_events(
        self, *, event_type: EventType, registered: bool | None = None
    ) -> Mapping[int | None, tuple[GenericEvent, ...]]:
        """Return a list of specific events of a channel."""
        events: dict[int | None, tuple[GenericEvent, ...]] = {}
        for channel in self._channels.values():
            if (values := channel.get_events(event_type=event_type, registered=registered)) and len(values) > 0:
                events[channel.no] = values
        return events

    def get_calculated_data_point(self, *, channel_address: str, parameter: str) -> CalculatedDataPoint | None:
        """Return a calculated data_point from device."""
        if channel := self.get_channel(channel_address=channel_address):
            return channel.get_calculated_data_point(parameter=parameter)
        return None

    def get_custom_data_point(self, *, channel_no: int) -> hmce.CustomDataPoint | None:
        """Return a custom data_point from device."""
        if channel := self.get_channel(
            channel_address=get_channel_address(device_address=self._address, channel_no=channel_no)
        ):
            return channel.custom_data_point
        return None

    def get_generic_data_point(
        self, *, channel_address: str, parameter: str, paramset_key: ParamsetKey | None = None
    ) -> GenericDataPoint | None:
        """Return a generic data_point from device."""
        if channel := self.get_channel(channel_address=channel_address):
            return channel.get_generic_data_point(parameter=parameter, paramset_key=paramset_key)
        return None

    def get_generic_event(self, *, channel_address: str, parameter: str) -> GenericEvent | None:
        """Return a generic event from device."""
        if channel := self.get_channel(channel_address=channel_address):
            return channel.get_generic_event(parameter=parameter)
        return None

    def get_readable_data_points(self, *, paramset_key: ParamsetKey) -> tuple[GenericDataPoint, ...]:
        """Return the list of readable master data points."""
        data_points: list[GenericDataPoint] = []
        for channel in self._channels.values():
            data_points.extend(channel.get_readable_data_points(paramset_key=paramset_key))
        return tuple(data_points)

    def set_forced_availability(self, *, forced_availability: ForcedDeviceAvailability) -> None:
        """Set the availability of the device."""
        if self._forced_availability != forced_availability:
            self._forced_availability = forced_availability
            for dp in self.generic_data_points:
                dp.fire_data_point_updated_callback()

    @inspector
    async def export_device_definition(self) -> None:
        """Export the device definition for current device."""
        try:
            device_exporter = _DefinitionExporter(device=self)
            await device_exporter.export_data()
        except Exception as exc:
            raise AioHomematicException(f"EXPORT_DEVICE_DEFINITION failed: {extract_exc_args(exc=exc)}") from exc

    def refresh_firmware_data(self) -> None:
        """Refresh firmware data of the device."""
        old_available_firmware = self.available_firmware
        old_firmware = self.firmware
        old_firmware_update_state = self.firmware_update_state
        old_firmware_updatable = self.firmware_updatable

        self._description = self._central.device_descriptions.get_device_description(
            interface_id=self._interface_id, address=self._address
        )

        if (
            old_available_firmware != self.available_firmware
            or old_firmware != self.firmware
            or old_firmware_update_state != self.firmware_update_state
            or old_firmware_updatable != self.firmware_updatable
        ):
            for callback_handler in self._firmware_update_callbacks:
                callback_handler()

    @inspector
    async def update_firmware(self, *, refresh_after_update_intervals: tuple[int, ...]) -> bool:
        """Update the firmware of the Homematic device."""
        update_result = await self._client.update_device_firmware(device_address=self._address)

        async def refresh_data() -> None:
            for refresh_interval in refresh_after_update_intervals:
                await asyncio.sleep(refresh_interval)
                await self._central.refresh_firmware_data(device_address=self._address)

        if refresh_after_update_intervals:
            self._central.looper.create_task(target=refresh_data(), name="refresh_firmware_data")

        return update_result

    @inspector
    async def load_value_cache(self) -> None:
        """Init the parameter cache."""
        if len(self.generic_data_points) > 0:
            await self._value_cache.init_base_data_points()
        if len(self.generic_events) > 0:
            await self._value_cache.init_readable_events()
        _LOGGER.debug(
            "INIT_DATA: Skipping load_data, missing data points for %s",
            self._address,
        )

    @inspector
    async def reload_paramset_descriptions(self) -> None:
        """Reload paramset for device."""
        for (
            paramset_key,
            channel_addresses,
        ) in self._central.paramset_descriptions.get_channel_addresses_by_paramset_key(
            interface_id=self._interface_id,
            device_address=self._address,
        ).items():
            for channel_address in channel_addresses:
                await self._client.fetch_paramset_description(
                    channel_address=channel_address,
                    paramset_key=paramset_key,
                )
        await self._central.save_files(save_paramset_descriptions=True)
        for dp in self.generic_data_points:
            dp.update_parameter_data()
        self.fire_device_updated_callback()

    @loop_check
    def fire_device_updated_callback(self) -> None:
        """Do what is needed when the state of the device has been updated."""
        self._set_modified_at()
        for callback_handler in self._device_updated_callbacks:
            try:
                callback_handler()
            except Exception as exc:
                _LOGGER.warning("FIRE_DEVICE_UPDATED failed: %s", extract_exc_args(exc=exc))

    def __str__(self) -> str:
        """Provide some useful information."""
        return (
            f"address: {self._address}, "
            f"model: {self._model}, "
            f"name: {self._name}, "
            f"generic dps: {len(self.generic_data_points)}, "
            f"calculated dps: {len(self.calculated_data_points)}, "
            f"custom dps: {len(self.custom_data_points)}, "
            f"events: {len(self.generic_events)}"
        )


class Channel(LogContextMixin, PayloadMixin):
    """Object to hold information about a channel and associated data points."""

    __slots__ = (
        "_address",
        "_calculated_data_points",
        "_central",
        "_custom_data_point",
        "_description",
        "_device",
        "_function",
        "_generic_data_points",
        "_generic_events",
        "_group_master",
        "_group_no",
        "_id",
        "_is_in_multi_group",
        "_modified_at",
        "_name_data",
        "_no",
        "_paramset_keys",
        "_rooms",
        "_type_name",
        "_unique_id",
    )

    def __init__(self, *, device: Device, channel_address: str) -> None:
        """Initialize the channel object."""
        PayloadMixin.__init__(self)

        self._device: Final = device
        self._central: Final = device.central
        self._address: Final = channel_address
        self._id: Final = self._central.device_details.get_address_id(address=channel_address)
        self._no: Final[int | None] = get_channel_no(address=channel_address)
        self._name_data: Final = get_channel_name_data(channel=self)
        self._description: DeviceDescription = self._central.device_descriptions.get_device_description(
            interface_id=self._device.interface_id, address=channel_address
        )
        self._type_name: Final[str] = self._description["TYPE"]
        self._paramset_keys: Final = tuple(ParamsetKey(paramset_key) for paramset_key in self._description["PARAMSETS"])

        self._unique_id: Final = generate_channel_unique_id(central=self._central, address=channel_address)
        self._group_no: int | None = None
        self._group_master: Channel | None = None
        self._is_in_multi_group: bool | None = None
        self._calculated_data_points: Final[dict[DataPointKey, CalculatedDataPoint]] = {}
        self._custom_data_point: hmce.CustomDataPoint | None = None
        self._generic_data_points: Final[dict[DataPointKey, GenericDataPoint]] = {}
        self._generic_events: Final[dict[DataPointKey, GenericEvent]] = {}
        self._modified_at: datetime = INIT_DATETIME
        self._rooms: Final = self._central.device_details.get_channel_rooms(channel_address=channel_address)
        self._function: Final = self._central.device_details.get_function_text(address=self._address)

    @info_property
    def address(self) -> str:
        """Return the address of the channel."""
        return self._address

    @property
    def calculated_data_points(self) -> tuple[CalculatedDataPoint, ...]:
        """Return the generic data points."""
        return tuple(self._calculated_data_points.values())

    @property
    def central(self) -> hmcu.CentralUnit:
        """Return the central."""
        return self._central

    @property
    def custom_data_point(self) -> hmce.CustomDataPoint | None:
        """Return the custom data point."""
        return self._custom_data_point

    @property
    def description(self) -> DeviceDescription:
        """Return the device description for the channel."""
        return self._description

    @hm_property(log_context=True)
    def device(self) -> Device:
        """Return the device of the channel."""
        return self._device

    @property
    def function(self) -> str | None:
        """Return the function of the channel."""
        return self._function

    @property
    def full_name(self) -> str:
        """Return the full name of the channel."""
        return self._name_data.full_name

    @property
    def generic_data_points(self) -> tuple[GenericDataPoint, ...]:
        """Return the generic data points."""
        return tuple(self._generic_data_points.values())

    @property
    def generic_events(self) -> tuple[GenericEvent, ...]:
        """Return the generic events."""
        return tuple(self._generic_events.values())

    @property
    def group_master(self) -> Channel | None:
        """Return the master channel of the group."""
        if self.group_no is None:
            return None
        if self._group_master is None:
            self._group_master = (
                self
                if self.is_group_master
                else self._device.get_channel(channel_address=f"{self._device.address}:{self.group_no}")
            )
        return self._group_master

    @property
    def group_no(self) -> int | None:
        """Return the no of the channel group."""
        if self._group_no is None:
            self._group_no = self._device.get_channel_group_no(channel_no=self._no)
        return self._group_no

    @property
    def id(self) -> str:
        """Return the id of the channel."""
        return self._id

    @property
    def is_in_multi_group(self) -> bool:
        """Return if multiple channels are in the group."""
        if self._is_in_multi_group is None:
            self._is_in_multi_group = self._device.is_in_multi_channel_group(channel_no=self._no)
        return self._is_in_multi_group

    @property
    def is_group_master(self) -> bool:
        """Return if group master of channel."""
        return self.group_no == self._no

    @property
    def name(self) -> str:
        """Return the name of the channel."""
        return self._name_data.channel_name

    @property
    def name_data(self) -> ChannelNameData:
        """Return the name data of the channel."""
        return self._name_data

    @hm_property(log_context=True)
    def no(self) -> int | None:
        """Return the channel_no of the channel."""
        return self._no

    @property
    def operation_mode(self) -> str | None:
        """Return the channel operation mode if available."""
        if (
            cop := self.get_generic_data_point(parameter=Parameter.CHANNEL_OPERATION_MODE)
        ) is not None and cop.value is not None:
            return str(cop.value)
        return None

    @property
    def paramset_keys(self) -> tuple[ParamsetKey, ...]:
        """Return the paramset_keys of the channel."""
        return self._paramset_keys

    @property
    def paramset_descriptions(self) -> Mapping[ParamsetKey, Mapping[str, ParameterData]]:
        """Return the paramset descriptions of the channel."""
        return self._central.paramset_descriptions.get_channel_paramset_descriptions(
            interface_id=self._device.interface_id, channel_address=self._address
        )

    @info_property
    def room(self) -> str | None:
        """Return the room of the device, if only one assigned in the backend."""
        if self._rooms and len(self._rooms) == 1:
            return list(self._rooms)[0]
        if self.is_group_master:
            return None
        if (master_channel := self.group_master) is not None:
            return master_channel.room
        return None

    @property
    def rooms(self) -> set[str]:
        """Return all rooms of the channel."""
        return self._rooms

    @property
    def type_name(self) -> str:
        """Return the type name of the channel."""
        return self._type_name

    @property
    def unique_id(self) -> str:
        """Return the unique_id of the channel."""
        return self._unique_id

    @inspector
    async def create_central_link(self) -> None:
        """Create a central link to support press events."""
        if self._has_key_press_events and not await self._has_central_link():
            await self._device.client.report_value_usage(
                address=self._address, value_id=REPORT_VALUE_USAGE_VALUE_ID, ref_counter=1
            )

    @inspector
    async def remove_central_link(self) -> None:
        """Remove a central link."""
        if self._has_key_press_events and await self._has_central_link() and not await self._has_program_ids():
            await self._device.client.report_value_usage(
                address=self._address, value_id=REPORT_VALUE_USAGE_VALUE_ID, ref_counter=0
            )

    @inspector
    async def cleanup_central_link_metadata(self) -> None:
        """Cleanup the metadata for central links."""
        if metadata := await self._device.client.get_metadata(address=self._address, data_id=REPORT_VALUE_USAGE_DATA):
            await self._device.client.set_metadata(
                address=self._address,
                data_id=REPORT_VALUE_USAGE_DATA,
                value={key: value for key, value in metadata.items() if key in CLICK_EVENTS},
            )

    async def _has_central_link(self) -> bool:
        """Check if central link exists."""
        try:
            if metadata := await self._device.client.get_metadata(
                address=self._address, data_id=REPORT_VALUE_USAGE_DATA
            ):
                return any(
                    key
                    for key, value in metadata.items()
                    if isinstance(key, str)
                    and isinstance(value, int)
                    and key == REPORT_VALUE_USAGE_VALUE_ID
                    and value > 0
                )
        except BaseHomematicException as bhexc:
            _LOGGER.debug("HAS_CENTRAL_LINK failed: %s", extract_exc_args(exc=bhexc))
        return False

    async def _has_program_ids(self) -> bool:
        """Return if a channel has program ids."""
        return bool(await self._device.client.has_program_ids(channel_hmid=self._id))

    @property
    def _has_key_press_events(self) -> bool:
        """Return if channel has KEYPRESS events."""
        return any(event for event in self.generic_events if event.event_type is EventType.KEYPRESS)

    def add_data_point(self, *, data_point: CallbackDataPoint) -> None:
        """Add a data_point to a channel."""
        if isinstance(data_point, BaseParameterDataPoint):
            self._central.add_event_subscription(data_point=data_point)
        if isinstance(data_point, CalculatedDataPoint):
            self._calculated_data_points[data_point.dpk] = data_point
        if isinstance(data_point, GenericDataPoint):
            self._generic_data_points[data_point.dpk] = data_point
            self._device.register_device_updated_callback(cb=data_point.fire_data_point_updated_callback)
        if isinstance(data_point, hmce.CustomDataPoint):
            self._custom_data_point = data_point
        if isinstance(data_point, GenericEvent):
            self._generic_events[data_point.dpk] = data_point

    def _remove_data_point(self, *, data_point: CallbackDataPoint) -> None:
        """Remove a data_point from a channel."""
        if isinstance(data_point, BaseParameterDataPoint):
            self._central.remove_event_subscription(data_point=data_point)
        if isinstance(data_point, CalculatedDataPoint):
            del self._calculated_data_points[data_point.dpk]
        if isinstance(data_point, GenericDataPoint):
            del self._generic_data_points[data_point.dpk]
            self._device.unregister_device_updated_callback(cb=data_point.fire_data_point_updated_callback)
        if isinstance(data_point, hmce.CustomDataPoint):
            self._custom_data_point = None
        if isinstance(data_point, GenericEvent):
            del self._generic_events[data_point.dpk]
        data_point.fire_device_removed_callback()

    def remove(self) -> None:
        """Remove data points from collections and central."""
        for event in self.generic_events:
            self._remove_data_point(data_point=event)
        self._generic_events.clear()

        for ccdp in self.calculated_data_points:
            self._remove_data_point(data_point=ccdp)
        self._calculated_data_points.clear()

        for gdp in self.generic_data_points:
            self._remove_data_point(data_point=gdp)
        self._generic_data_points.clear()

        if self._custom_data_point:
            self._remove_data_point(data_point=self._custom_data_point)

    def _set_modified_at(self) -> None:
        self._modified_at = datetime.now()

    def get_data_points(
        self,
        *,
        category: DataPointCategory | None = None,
        exclude_no_create: bool = True,
        registered: bool | None = None,
    ) -> tuple[CallbackDataPoint, ...]:
        """Get all data points of the device."""
        all_data_points: list[CallbackDataPoint] = list(self._generic_data_points.values()) + list(
            self._calculated_data_points.values()
        )
        if self._custom_data_point:
            all_data_points.append(self._custom_data_point)

        return tuple(
            dp
            for dp in all_data_points
            if dp is not None
            and (category is None or dp.category == category)
            and ((exclude_no_create and dp.usage != DataPointUsage.NO_CREATE) or exclude_no_create is False)
            and (registered is None or dp.is_registered == registered)
        )

    def get_events(self, *, event_type: EventType, registered: bool | None = None) -> tuple[GenericEvent, ...]:
        """Return a list of specific events of a channel."""
        return tuple(
            event
            for event in self._generic_events.values()
            if (event.event_type == event_type and (registered is None or event.is_registered == registered))
        )

    def get_calculated_data_point(self, *, parameter: str) -> CalculatedDataPoint | None:
        """Return a calculated data_point from device."""
        return self._calculated_data_points.get(
            DataPointKey(
                interface_id=self._device.interface_id,
                channel_address=self._address,
                paramset_key=ParamsetKey.CALCULATED,
                parameter=parameter,
            )
        )

    def get_generic_data_point(
        self, *, parameter: str, paramset_key: ParamsetKey | None = None
    ) -> GenericDataPoint | None:
        """Return a generic data_point from device."""
        if paramset_key:
            return self._generic_data_points.get(
                DataPointKey(
                    interface_id=self._device.interface_id,
                    channel_address=self._address,
                    paramset_key=paramset_key,
                    parameter=parameter,
                )
            )

        if dp := self._generic_data_points.get(
            DataPointKey(
                interface_id=self._device.interface_id,
                channel_address=self._address,
                paramset_key=ParamsetKey.VALUES,
                parameter=parameter,
            )
        ):
            return dp
        return self._generic_data_points.get(
            DataPointKey(
                interface_id=self._device.interface_id,
                channel_address=self._address,
                paramset_key=ParamsetKey.MASTER,
                parameter=parameter,
            )
        )

    def get_generic_event(self, *, parameter: str) -> GenericEvent | None:
        """Return a generic event from device."""
        return self._generic_events.get(
            DataPointKey(
                interface_id=self._device.interface_id,
                channel_address=self._address,
                paramset_key=ParamsetKey.VALUES,
                parameter=parameter,
            )
        )

    def get_readable_data_points(self, *, paramset_key: ParamsetKey) -> tuple[GenericDataPoint, ...]:
        """Return the list of readable master data points."""
        return tuple(
            ge for ge in self._generic_data_points.values() if ge.is_readable and ge.paramset_key == paramset_key
        )

    def __str__(self) -> str:
        """Provide some useful information."""
        return (
            f"address: {self._address}, "
            f"type: {self._type_name}, "
            f"generic dps: {len(self._generic_data_points)}, "
            f"calculated dps: {len(self._calculated_data_points)}, "
            f"custom dp: {self._custom_data_point is not None}, "
            f"events: {len(self._generic_events)}"
        )


class _ValueCache:
    """A Cache to temporarily stored values."""

    __slots__ = (
        "_device",
        "_device_cache",
        "_sema_get_or_load_value",
    )

    _NO_VALUE_CACHE_ENTRY: Final = "NO_VALUE_CACHE_ENTRY"

    def __init__(self, *, device: Device) -> None:
        """Init the value cache."""
        self._sema_get_or_load_value: Final = asyncio.Semaphore()
        self._device: Final = device
        # {key, CacheEntry}
        self._device_cache: Final[dict[DataPointKey, CacheEntry]] = {}

    async def init_base_data_points(self) -> None:
        """Load data by get_value."""
        try:
            for dp in self._get_base_data_points():
                await dp.load_data_point_value(call_source=CallSource.HM_INIT)
        except BaseHomematicException as bhexc:
            _LOGGER.debug(
                "init_base_data_points: Failed to init cache for channel0 %s, %s [%s]",
                self._device.model,
                self._device.address,
                extract_exc_args(exc=bhexc),
            )

    def _get_base_data_points(self) -> set[GenericDataPoint]:
        """Get data points of channel 0 and master."""
        return {
            dp
            for dp in self._device.generic_data_points
            if (
                dp.channel.no == 0
                and dp.paramset_key == ParamsetKey.VALUES
                and dp.parameter in RELEVANT_INIT_PARAMETERS
            )
            or dp.paramset_key == ParamsetKey.MASTER
        }

    async def init_readable_events(self) -> None:
        """Load data by get_value."""
        try:
            for event in self._get_readable_events():
                await event.load_data_point_value(call_source=CallSource.HM_INIT)
        except BaseHomematicException as bhexc:
            _LOGGER.debug(
                "init_base_events: Failed to init cache for channel0 %s, %s [%s]",
                self._device.model,
                self._device.address,
                extract_exc_args(exc=bhexc),
            )

    def _get_readable_events(self) -> set[GenericEvent]:
        """Get readable events."""
        return {event for event in self._device.generic_events if event.is_readable}

    async def get_value(
        self,
        *,
        dpk: DataPointKey,
        call_source: CallSource,
        direct_call: bool = False,
    ) -> Any:
        """Load data."""

        async with self._sema_get_or_load_value:
            if direct_call is False and (cached_value := self._get_value_from_cache(dpk=dpk)) != NO_CACHE_ENTRY:
                return NO_CACHE_ENTRY if cached_value == self._NO_VALUE_CACHE_ENTRY else cached_value

            value_dict: dict[str, Any] = {dpk.parameter: self._NO_VALUE_CACHE_ENTRY}
            try:
                value_dict = await self._get_values_for_cache(dpk=dpk)
            except BaseHomematicException as bhexc:
                _LOGGER.debug(
                    "GET_OR_LOAD_VALUE: Failed to get data for %s, %s, %s, %s: %s",
                    self._device.model,
                    dpk.channel_address,
                    dpk.parameter,
                    call_source,
                    extract_exc_args(exc=bhexc),
                )
            for d_parameter, d_value in value_dict.items():
                self._add_entry_to_device_cache(
                    dpk=DataPointKey(
                        interface_id=dpk.interface_id,
                        channel_address=dpk.channel_address,
                        paramset_key=dpk.paramset_key,
                        parameter=d_parameter,
                    ),
                    value=d_value,
                )
            return (
                NO_CACHE_ENTRY
                if (value := value_dict.get(dpk.parameter)) and value == self._NO_VALUE_CACHE_ENTRY
                else value
            )

    async def _get_values_for_cache(self, *, dpk: DataPointKey) -> dict[str, Any]:
        """Return a value from the backend to store in cache."""
        if not self._device.available:
            _LOGGER.debug(
                "GET_VALUES_FOR_CACHE failed: device %s (%s) is not available", self._device.name, self._device.address
            )
            return {}
        if dpk.paramset_key == ParamsetKey.VALUES:
            return {
                dpk.parameter: await self._device.client.get_value(
                    channel_address=dpk.channel_address,
                    paramset_key=dpk.paramset_key,
                    parameter=dpk.parameter,
                    call_source=CallSource.HM_INIT,
                )
            }
        return await self._device.client.get_paramset(
            address=dpk.channel_address, paramset_key=dpk.paramset_key, call_source=CallSource.HM_INIT
        )

    def _add_entry_to_device_cache(self, *, dpk: DataPointKey, value: Any) -> None:
        """Add value to cache."""
        # write value to cache even if an exception has occurred
        # to avoid repetitive calls to the backend within max_age
        self._device_cache[dpk] = CacheEntry(value=value, refresh_at=datetime.now())

    def _get_value_from_cache(
        self,
        *,
        dpk: DataPointKey,
    ) -> Any:
        """Load data from store."""
        # Try to get data from central cache
        if (
            dpk.paramset_key == ParamsetKey.VALUES
            and (
                global_value := self._device.central.data_cache.get_data(
                    interface=self._device.interface,
                    channel_address=dpk.channel_address,
                    parameter=dpk.parameter,
                )
            )
            != NO_CACHE_ENTRY
        ):
            return global_value

        if (cache_entry := self._device_cache.get(dpk, CacheEntry.empty())) and cache_entry.is_valid:
            return cache_entry.value
        return NO_CACHE_ENTRY


class _DefinitionExporter:
    """Export device definitions from cache."""

    __slots__ = (
        "_central",
        "_client",
        "_device_address",
        "_interface_id",
        "_random_id",
        "_storage_directory",
    )

    def __init__(self, *, device: Device) -> None:
        """Init the device exporter."""
        self._client: Final = device.client
        self._central: Final = device.client.central
        self._storage_directory: Final = self._central.config.storage_directory
        self._interface_id: Final = device.interface_id
        self._device_address: Final = device.address
        self._random_id: Final[str] = f"VCU{int(random.randint(1000000, 9999999))}"

    @inspector
    async def export_data(self) -> None:
        """Export data."""
        device_descriptions: Mapping[str, DeviceDescription] = (
            self._central.device_descriptions.get_device_with_channels(
                interface_id=self._interface_id, device_address=self._device_address
            )
        )
        paramset_descriptions: dict[
            str, dict[ParamsetKey, dict[str, ParameterData]]
        ] = await self._client.get_all_paramset_descriptions(device_descriptions=tuple(device_descriptions.values()))
        model = device_descriptions[self._device_address]["TYPE"]
        file_name = f"{model}.json"

        # anonymize device_descriptions
        anonymize_device_descriptions: list[DeviceDescription] = []
        for device_description in device_descriptions.values():
            new_device_description: DeviceDescription = device_description.copy()
            new_device_description["ADDRESS"] = self._anonymize_address(address=new_device_description["ADDRESS"])
            if new_device_description.get("PARENT"):
                new_device_description["PARENT"] = new_device_description["ADDRESS"].split(ADDRESS_SEPARATOR)[0]
            elif new_device_description.get("CHILDREN"):
                new_device_description["CHILDREN"] = [
                    self._anonymize_address(address=a) for a in new_device_description["CHILDREN"]
                ]
            anonymize_device_descriptions.append(new_device_description)

        # anonymize paramset_descriptions
        anonymize_paramset_descriptions: dict[str, dict[ParamsetKey, dict[str, ParameterData]]] = {}
        for address, paramset_description in paramset_descriptions.items():
            anonymize_paramset_descriptions[self._anonymize_address(address=address)] = paramset_description

        # Save device_descriptions for device to file.
        await self._save(
            directory=f"{self._storage_directory}/{DEVICE_DESCRIPTIONS_DIR}",
            file_name=file_name,
            data=anonymize_device_descriptions,
        )

        # Save device_descriptions for device to file.
        await self._save(
            directory=f"{self._storage_directory}/{PARAMSET_DESCRIPTIONS_DIR}",
            file_name=file_name,
            data=anonymize_paramset_descriptions,
        )

    def _anonymize_address(self, *, address: str) -> str:
        address_parts = address.split(ADDRESS_SEPARATOR)
        address_parts[0] = self._random_id
        return ADDRESS_SEPARATOR.join(address_parts)

    async def _save(self, *, directory: str, file_name: str, data: Any) -> DataOperationResult:
        """Save file to disk."""

        def perform_save() -> DataOperationResult:
            if not check_or_create_directory(directory=directory):
                return DataOperationResult.NO_SAVE  # pragma: no cover
            with open(file=os.path.join(directory, file_name), mode="wb") as fptr:
                fptr.write(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS))
            return DataOperationResult.SAVE_SUCCESS

        return await self._central.looper.async_add_executor_job(perform_save, name="save-device-description")
