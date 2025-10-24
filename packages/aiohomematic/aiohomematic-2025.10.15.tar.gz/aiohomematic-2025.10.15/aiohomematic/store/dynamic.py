# SPDX-License-Identifier: MIT
# Copyright (c) 2021-2025
"""
Dynamic store used at runtime by the central unit and clients.

This module provides short-lived, in-memory store that support robust and efficient
communication with Homematic interfaces:

- CommandCache: Tracks recently sent commands and their values per data point,
  allowing suppression of immediate echo updates or reconciliation with incoming
  events. Supports set_value, put_paramset, and combined parameters.
- DeviceDetailsCache: Enriches devices with human-readable names, interface
  mapping, rooms, functions, and address IDs fetched via the backend.
- CentralDataCache: Stores recently fetched device/channel parameter values from
  interfaces for quick lookup and periodic refresh.
- PingPongCache: Tracks ping/pong timestamps to detect connection health issues
  and emits interface events on mismatch thresholds.

The store are intentionally ephemeral and cleared/aged according to the rules in
constants to keep memory footprint predictable while improving responsiveness.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime
import logging
from typing import Any, Final, cast

from aiohomematic import central as hmcu
from aiohomematic.const import (
    DP_KEY_VALUE,
    INIT_DATETIME,
    LAST_COMMAND_SEND_STORE_TIMEOUT,
    MAX_CACHE_AGE,
    NO_CACHE_ENTRY,
    PING_PONG_MISMATCH_COUNT,
    PING_PONG_MISMATCH_COUNT_TTL,
    CallSource,
    DataPointKey,
    EventKey,
    EventType,
    Interface,
    InterfaceEventType,
    ParamsetKey,
)
from aiohomematic.converter import CONVERTABLE_PARAMETERS, convert_combined_parameter_to_paramset
from aiohomematic.model.device import Device
from aiohomematic.support import changed_within_seconds, get_device_address

_LOGGER: Final = logging.getLogger(__name__)


class CommandCache:
    """Cache for send commands."""

    __slots__ = (
        "_interface_id",
        "_last_send_command",
    )

    def __init__(self, *, interface_id: str) -> None:
        """Init command cache."""
        self._interface_id: Final = interface_id
        # (paramset_key, device_address, channel_no, parameter)
        self._last_send_command: Final[dict[DataPointKey, tuple[Any, datetime]]] = {}

    def add_set_value(
        self,
        *,
        channel_address: str,
        parameter: str,
        value: Any,
    ) -> set[DP_KEY_VALUE]:
        """Add data from set value command."""
        if parameter in CONVERTABLE_PARAMETERS:
            return self.add_combined_parameter(
                parameter=parameter, channel_address=channel_address, combined_parameter=value
            )

        now_ts = datetime.now()
        dpk = DataPointKey(
            interface_id=self._interface_id,
            channel_address=channel_address,
            paramset_key=ParamsetKey.VALUES,
            parameter=parameter,
        )
        self._last_send_command[dpk] = (value, now_ts)
        return {(dpk, value)}

    def add_put_paramset(
        self, *, channel_address: str, paramset_key: ParamsetKey, values: dict[str, Any]
    ) -> set[DP_KEY_VALUE]:
        """Add data from put paramset command."""
        dpk_values: set[DP_KEY_VALUE] = set()
        now_ts = datetime.now()
        for parameter, value in values.items():
            dpk = DataPointKey(
                interface_id=self._interface_id,
                channel_address=channel_address,
                paramset_key=paramset_key,
                parameter=parameter,
            )
            self._last_send_command[dpk] = (value, now_ts)
            dpk_values.add((dpk, value))
        return dpk_values

    def add_combined_parameter(
        self, *, parameter: str, channel_address: str, combined_parameter: str
    ) -> set[DP_KEY_VALUE]:
        """Add data from combined parameter."""
        if values := convert_combined_parameter_to_paramset(parameter=parameter, value=combined_parameter):
            return self.add_put_paramset(
                channel_address=channel_address,
                paramset_key=ParamsetKey.VALUES,
                values=values,
            )
        return set()

    def get_last_value_send(self, *, dpk: DataPointKey, max_age: int = LAST_COMMAND_SEND_STORE_TIMEOUT) -> Any:
        """Return the last send values."""
        if result := self._last_send_command.get(dpk):
            value, last_send_dt = result
            if last_send_dt and changed_within_seconds(last_change=last_send_dt, max_age=max_age):
                return value
            self.remove_last_value_send(
                dpk=dpk,
                max_age=max_age,
            )
        return None

    def remove_last_value_send(
        self,
        *,
        dpk: DataPointKey,
        value: Any = None,
        max_age: int = LAST_COMMAND_SEND_STORE_TIMEOUT,
    ) -> None:
        """Remove the last send value."""
        if result := self._last_send_command.get(dpk):
            stored_value, last_send_dt = result
            if not changed_within_seconds(last_change=last_send_dt, max_age=max_age) or (
                value is not None and stored_value == value
            ):
                del self._last_send_command[dpk]


class DeviceDetailsCache:
    """Cache for device/channel details."""

    __slots__ = (
        "_central",
        "_channel_rooms",
        "_device_channel_ids",
        "_device_rooms",
        "_functions",
        "_interface_cache",
        "_names_cache",
        "_refreshed_at",
    )

    def __init__(self, *, central: hmcu.CentralUnit) -> None:
        """Init the device details cache."""
        self._central: Final = central
        self._channel_rooms: Final[dict[str, set[str]]] = defaultdict(set)
        self._device_channel_ids: Final[dict[str, str]] = {}
        self._device_rooms: Final[dict[str, set[str]]] = defaultdict(set)
        self._functions: Final[dict[str, set[str]]] = {}
        self._interface_cache: Final[dict[str, Interface]] = {}
        self._names_cache: Final[dict[str, str]] = {}
        self._refreshed_at = INIT_DATETIME

    async def load(self, *, direct_call: bool = False) -> None:
        """Fetch names from the backend."""
        if direct_call is False and changed_within_seconds(
            last_change=self._refreshed_at, max_age=int(MAX_CACHE_AGE / 3)
        ):
            return
        self.clear()
        _LOGGER.debug("LOAD: Loading names for %s", self._central.name)
        if client := self._central.primary_client:
            await client.fetch_device_details()
        _LOGGER.debug("LOAD: Loading rooms for %s", self._central.name)
        self._channel_rooms.clear()
        self._channel_rooms.update(await self._get_all_rooms())
        self._device_rooms.clear()
        self._device_rooms.update(self._prepare_device_rooms())
        _LOGGER.debug("LOAD: Loading functions for %s", self._central.name)
        self._functions.clear()
        self._functions.update(await self._get_all_functions())
        self._refreshed_at = datetime.now()

    @property
    def device_channel_ids(self) -> Mapping[str, str]:
        """Return device channel ids."""
        return self._device_channel_ids

    def add_name(self, *, address: str, name: str) -> None:
        """Add name to cache."""
        self._names_cache[address] = name

    def get_name(self, *, address: str) -> str | None:
        """Get name from cache."""
        return self._names_cache.get(address)

    def add_interface(self, *, address: str, interface: Interface) -> None:
        """Add interface to cache."""
        self._interface_cache[address] = interface

    def get_interface(self, *, address: str) -> Interface:
        """Get interface from cache."""
        return self._interface_cache.get(address) or Interface.BIDCOS_RF

    def add_address_id(self, *, address: str, hmid: str) -> None:
        """Add channel id for a channel."""
        self._device_channel_ids[address] = hmid

    def get_address_id(self, *, address: str) -> str:
        """Get id for address."""
        return self._device_channel_ids.get(address) or "0"

    async def _get_all_rooms(self) -> Mapping[str, set[str]]:
        """Get all rooms, if available."""
        if client := self._central.primary_client:
            return await client.get_all_rooms()
        return {}

    def _prepare_device_rooms(self) -> dict[str, set[str]]:
        """Return rooms by device_address."""
        _device_rooms: Final[dict[str, set[str]]] = defaultdict(set)
        for channel_address, rooms in self._channel_rooms.items():
            if rooms:
                _device_rooms[get_device_address(address=channel_address)].update(rooms)
        return _device_rooms

    def get_device_rooms(self, *, device_address: str) -> set[str]:
        """Return all rooms by device_address."""
        return set(self._device_rooms.get(device_address, ()))

    def get_channel_rooms(self, *, channel_address: str) -> set[str]:
        """Return rooms by channel_address."""
        return self._channel_rooms[channel_address]

    async def _get_all_functions(self) -> Mapping[str, set[str]]:
        """Get all functions, if available."""
        if client := self._central.primary_client:
            return await client.get_all_functions()
        return {}

    def get_function_text(self, *, address: str) -> str | None:
        """Return function by address."""
        if functions := self._functions.get(address):
            return ",".join(functions)
        return None

    def remove_device(self, *, device: Device) -> None:
        """Remove name from cache."""
        if device.address in self._names_cache:
            del self._names_cache[device.address]
        for channel_address in device.channels:
            if channel_address in self._names_cache:
                del self._names_cache[channel_address]

    def clear(self) -> None:
        """Clear the cache."""
        self._names_cache.clear()
        self._channel_rooms.clear()
        self._device_rooms.clear()
        self._functions.clear()
        self._refreshed_at = INIT_DATETIME


class CentralDataCache:
    """Central cache for device/channel initial data."""

    __slots__ = (
        "_central",
        "_refreshed_at",
        "_value_cache",
    )

    def __init__(self, *, central: hmcu.CentralUnit) -> None:
        """Init the central data cache."""
        self._central: Final = central
        # { key, value}
        self._value_cache: Final[dict[Interface, Mapping[str, Any]]] = {}
        self._refreshed_at: Final[dict[Interface, datetime]] = {}

    async def load(self, *, direct_call: bool = False, interface: Interface | None = None) -> None:
        """Fetch data from the backend."""
        _LOGGER.debug("load: Loading device data for %s", self._central.name)
        for client in self._central.clients:
            if interface and interface != client.interface:
                continue
            if direct_call is False and changed_within_seconds(
                last_change=self._get_refreshed_at(interface=client.interface),
                max_age=int(MAX_CACHE_AGE / 3),
            ):
                return
            await client.fetch_all_device_data()

    async def refresh_data_point_data(
        self,
        *,
        paramset_key: ParamsetKey | None = None,
        interface: Interface | None = None,
        direct_call: bool = False,
    ) -> None:
        """Refresh data_point data."""
        for dp in self._central.get_readable_generic_data_points(paramset_key=paramset_key, interface=interface):
            await dp.load_data_point_value(call_source=CallSource.HM_INIT, direct_call=direct_call)

    def add_data(self, *, interface: Interface, all_device_data: Mapping[str, Any]) -> None:
        """Add data to cache."""
        self._value_cache[interface] = all_device_data
        self._refreshed_at[interface] = datetime.now()

    def get_data(
        self,
        *,
        interface: Interface,
        channel_address: str,
        parameter: str,
    ) -> Any:
        """Get data from cache."""
        if not self._is_empty(interface=interface) and (iface_cache := self._value_cache.get(interface)) is not None:
            return iface_cache.get(f"{interface}.{channel_address}.{parameter}", NO_CACHE_ENTRY)
        return NO_CACHE_ENTRY

    def clear(self, *, interface: Interface | None = None) -> None:
        """Clear the cache."""
        if interface:
            self._value_cache[interface] = {}
            self._refreshed_at[interface] = INIT_DATETIME
        else:
            for _interface in self._central.interfaces:
                self.clear(interface=_interface)

    def _get_refreshed_at(self, *, interface: Interface) -> datetime:
        """Return when cache has been refreshed."""
        return self._refreshed_at.get(interface, INIT_DATETIME)

    def _is_empty(self, *, interface: Interface) -> bool:
        """Return if cache is empty for the given interface."""
        # If there is no data stored for the requested interface, treat as empty.
        if not self._value_cache.get(interface):
            return True
        # Auto-expire stale cache by interface.
        if not changed_within_seconds(last_change=self._get_refreshed_at(interface=interface)):
            self.clear(interface=interface)
            return True
        return False


class PingPongCache:
    """Cache to collect ping/pong events with ttl."""

    __slots__ = (
        "_allowed_delta",
        "_central",
        "_interface_id",
        "_pending_pong_logged",
        "_pending_pongs",
        "_ttl",
        "_unknown_pong_logged",
        "_unknown_pongs",
    )

    def __init__(
        self,
        *,
        central: hmcu.CentralUnit,
        interface_id: str,
        allowed_delta: int = PING_PONG_MISMATCH_COUNT,
        ttl: int = PING_PONG_MISMATCH_COUNT_TTL,
    ):
        """Initialize the cache with ttl."""
        assert ttl > 0
        self._central: Final = central
        self._interface_id: Final = interface_id
        self._allowed_delta: Final = allowed_delta
        self._ttl: Final = ttl
        self._pending_pongs: Final[set[datetime]] = set()
        self._unknown_pongs: Final[set[datetime]] = set()
        self._pending_pong_logged: bool = False
        self._unknown_pong_logged: bool = False

    @property
    def high_pending_pongs(self) -> bool:
        """Check, if store contains too many pending pongs."""
        self._cleanup_pending_pongs()
        return len(self._pending_pongs) > self._allowed_delta

    @property
    def high_unknown_pongs(self) -> bool:
        """Check, if store contains too many unknown pongs."""
        self._cleanup_unknown_pongs()
        return len(self._unknown_pongs) > self._allowed_delta

    @property
    def low_pending_pongs(self) -> bool:
        """Return True when pending pong count is at or below the allowed delta (i.e., not high)."""
        self._cleanup_pending_pongs()
        return len(self._pending_pongs) <= self._allowed_delta

    @property
    def low_unknown_pongs(self) -> bool:
        """Return True when unknown pong count is at or below the allowed delta (i.e., not high)."""
        self._cleanup_unknown_pongs()
        return len(self._unknown_pongs) <= self._allowed_delta

    @property
    def pending_pong_count(self) -> int:
        """Return the pending pong count."""
        return len(self._pending_pongs)

    @property
    def unknown_pong_count(self) -> int:
        """Return the unknown pong count."""
        return len(self._unknown_pongs)

    def clear(self) -> None:
        """Clear the cache."""
        self._pending_pongs.clear()
        self._unknown_pongs.clear()
        self._pending_pong_logged = False
        self._unknown_pong_logged = False

    def handle_send_ping(self, *, ping_ts: datetime) -> None:
        """Handle send ping timestamp."""
        self._pending_pongs.add(ping_ts)
        # Throttle event emission to every second ping to avoid spamming callbacks,
        # but always emit when crossing the high threshold.
        count = self.pending_pong_count
        if (count > self._allowed_delta) or (count % 2 == 0):
            self._check_and_fire_pong_event(
                event_type=InterfaceEventType.PENDING_PONG,
                pong_mismatch_count=count,
            )
        _LOGGER.debug(
            "PING PONG CACHE: Increase pending PING count: %s - %i for ts: %s",
            self._interface_id,
            self.pending_pong_count,
            ping_ts,
        )

    def handle_received_pong(self, *, pong_ts: datetime) -> None:
        """Handle received pong timestamp."""
        if pong_ts in self._pending_pongs:
            self._pending_pongs.remove(pong_ts)
            self._check_and_fire_pong_event(
                event_type=InterfaceEventType.PENDING_PONG,
                pong_mismatch_count=self.pending_pong_count,
            )
            _LOGGER.debug(
                "PING PONG CACHE: Reduce pending PING count: %s - %i for ts: %s",
                self._interface_id,
                self.pending_pong_count,
                pong_ts,
            )
            return

        self._unknown_pongs.add(pong_ts)
        self._check_and_fire_pong_event(
            event_type=InterfaceEventType.UNKNOWN_PONG,
            pong_mismatch_count=self.unknown_pong_count,
        )
        _LOGGER.debug(
            "PING PONG CACHE: Increase unknown PONG count: %s - %i for ts: %s",
            self._interface_id,
            self.unknown_pong_count,
            pong_ts,
        )

    def _cleanup_pending_pongs(self) -> None:
        """Cleanup too old pending pongs."""
        dt_now = datetime.now()
        for pong_ts in list(self._pending_pongs):
            # Only expire entries that are actually older than the TTL.
            if (dt_now - pong_ts).total_seconds() > self._ttl:
                self._pending_pongs.remove(pong_ts)
                _LOGGER.debug(
                    "PING PONG CACHE: Removing expired pending PONG: %s - %i for ts: %s",
                    self._interface_id,
                    self.pending_pong_count,
                    pong_ts,
                )

    def _cleanup_unknown_pongs(self) -> None:
        """Cleanup too old unknown pongs."""
        dt_now = datetime.now()
        for pong_ts in list(self._unknown_pongs):
            # Only expire entries that are actually older than the TTL.
            if (dt_now - pong_ts).total_seconds() > self._ttl:
                self._unknown_pongs.remove(pong_ts)
                _LOGGER.debug(
                    "PING PONG CACHE: Removing expired unknown PONG: %s - %i or ts: %s",
                    self._interface_id,
                    self.unknown_pong_count,
                    pong_ts,
                )

    def _check_and_fire_pong_event(self, *, event_type: InterfaceEventType, pong_mismatch_count: int) -> None:
        """Fire an event about the pong status."""

        def _fire_event(mismatch_count: int) -> None:
            self._central.fire_homematic_callback(
                event_type=EventType.INTERFACE,
                event_data=cast(
                    dict[EventKey, Any],
                    hmcu.INTERFACE_EVENT_SCHEMA(
                        {
                            EventKey.INTERFACE_ID: self._interface_id,
                            EventKey.TYPE: event_type,
                            EventKey.DATA: {
                                EventKey.CENTRAL_NAME: self._central.name,
                                EventKey.PONG_MISMATCH_COUNT: mismatch_count,
                            },
                        }
                    ),
                ),
            )

        if self.low_pending_pongs and event_type == InterfaceEventType.PENDING_PONG:
            # In low state:
            # - If we previously logged a high state, emit a reset event (mismatch=0) exactly once.
            # - Otherwise, throttle emission to every second ping (even counts > 0) to avoid spamming.
            if self._pending_pong_logged:
                _fire_event(mismatch_count=0)
                self._pending_pong_logged = False
                return
            if pong_mismatch_count > 0 and pong_mismatch_count % 2 == 0:
                _fire_event(mismatch_count=pong_mismatch_count)
            return

        if self.low_unknown_pongs and event_type == InterfaceEventType.UNKNOWN_PONG:
            # For unknown pongs, only reset the logged flag when we drop below the threshold.
            # We do not emit an event here since there is no explicit expectation for a reset notification.
            self._unknown_pong_logged = False
            return

        if self.high_pending_pongs and event_type == InterfaceEventType.PENDING_PONG:
            _fire_event(mismatch_count=pong_mismatch_count)
            if self._pending_pong_logged is False:
                _LOGGER.warning(
                    "Pending PONG mismatch: There is a mismatch between send ping events and received pong events for instance %s. "
                    "Possible reason 1: You are running multiple instances with the same instance name configured for this integration. "
                    "Re-add one instance! Otherwise this instance will not receive update events from your CCU. "
                    "Possible reason 2: Something is stuck on the CCU or hasn't been cleaned up. Therefore, try a CCU restart."
                    "Possible reason 3: Your setup is misconfigured and this instance is not able to receive events from the CCU.",
                    self._interface_id,
                )
            self._pending_pong_logged = True

        if self.high_unknown_pongs and event_type == InterfaceEventType.UNKNOWN_PONG:
            if self._unknown_pong_logged is False:
                _LOGGER.warning(
                    "Unknown PONG Mismatch: Your instance %s receives PONG events, that it hasn't send. "
                    "Possible reason 1: You are running multiple instances with the same instance name configured for this integration. "
                    "Re-add one instance! Otherwise the other instance will not receive update events from your CCU. "
                    "Possible reason 2: Something is stuck on the CCU or hasn't been cleaned up. Therefore, try a CCU restart.",
                    self._interface_id,
                )
            self._unknown_pong_logged = True
