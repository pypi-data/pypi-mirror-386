# SPDX-License-Identifier: MIT
# Copyright (c) 2021-2025
"""Support for data points used within aiohomematic."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping
from enum import StrEnum
from functools import lru_cache
import logging
from typing import Any, Final

from aiohomematic import central as hmcu
from aiohomematic.const import (
    ADDRESS_SEPARATOR,
    PROGRAM_ADDRESS,
    PROGRAM_SET_PATH_ROOT,
    PROGRAM_STATE_PATH_ROOT,
    SET_PATH_ROOT,
    STATE_PATH_ROOT,
    SYSVAR_ADDRESS,
    SYSVAR_SET_PATH_ROOT,
    SYSVAR_STATE_PATH_ROOT,
    SYSVAR_TYPE,
    VIRTDEV_SET_PATH_ROOT,
    VIRTDEV_STATE_PATH_ROOT,
    VIRTUAL_REMOTE_ADDRESSES,
    DataPointUsage,
    Interface,
    ParameterData,
    ParameterType,
)
from aiohomematic.model import device as hmd
from aiohomematic.model.custom import definition as hmed
from aiohomematic.support import to_bool

__all__ = [
    "ChannelNameData",
    "DataPointNameData",
    "GenericParameterType",
    "check_channel_is_the_only_primary_channel",
    "convert_value",
    "generate_channel_unique_id",
    "generate_unique_id",
    "get_channel_name_data",
    "get_custom_data_point_name",
    "get_device_name",
    "get_data_point_name_data",
    "get_event_name",
    "get_index_of_value_from_value_list",
    "get_value_from_value_list",
    "is_binary_sensor",
]
_LOGGER: Final = logging.getLogger(__name__)

type GenericParameterType = bool | int | float | str | None

# dict with binary_sensor relevant value lists and the corresponding TRUE value
_BINARY_SENSOR_TRUE_VALUE_DICT_FOR_VALUE_LIST: Final[Mapping[tuple[str, ...], str]] = {
    ("CLOSED", "OPEN"): "OPEN",
    ("DRY", "RAIN"): "RAIN",
    ("STABLE", "NOT_STABLE"): "NOT_STABLE",
}


class ChannelNameData:
    """Dataclass for channel name parts."""

    __slots__ = (
        "channel_name",
        "device_name",
        "full_name",
        "sub_device_name",
    )

    def __init__(self, *, device_name: str, channel_name: str) -> None:
        """Init the DataPointNameData class."""
        self.device_name: Final = device_name
        self.channel_name: Final = self._get_channel_name(device_name=device_name, channel_name=channel_name)
        self.full_name = f"{device_name} {self.channel_name}".strip() if self.channel_name else device_name
        self.sub_device_name = channel_name if channel_name else device_name

    @staticmethod
    def empty() -> ChannelNameData:
        """Return an empty DataPointNameData."""
        return ChannelNameData(device_name="", channel_name="")

    @staticmethod
    def _get_channel_name(*, device_name: str, channel_name: str) -> str:
        """Return the channel_name of the data_point only name."""
        if device_name and channel_name and channel_name.startswith(device_name):
            c_name = channel_name.replace(device_name, "").strip()
            if c_name.startswith(ADDRESS_SEPARATOR):
                c_name = c_name[1:]
            return c_name
        return channel_name.strip()


class DataPointNameData(ChannelNameData):
    """Dataclass for data_point name parts."""

    __slots__ = (
        "name",
        "parameter_name",
    )

    def __init__(self, *, device_name: str, channel_name: str, parameter_name: str | None = None) -> None:
        """Init the DataPointNameData class."""
        super().__init__(device_name=device_name, channel_name=channel_name)

        self.name: Final = self._get_data_point_name(
            device_name=device_name, channel_name=channel_name, parameter_name=parameter_name
        )
        self.full_name = f"{device_name} {self.name}".strip() if self.name else device_name
        self.parameter_name = parameter_name

    @staticmethod
    def empty() -> DataPointNameData:
        """Return an empty DataPointNameData."""
        return DataPointNameData(device_name="", channel_name="")

    @staticmethod
    def _get_channel_parameter_name(*, channel_name: str, parameter_name: str | None) -> str:
        """Return the channel parameter name of the data_point."""
        if channel_name and parameter_name:
            return f"{channel_name} {parameter_name}".strip()
        return channel_name.strip()

    def _get_data_point_name(self, *, device_name: str, channel_name: str, parameter_name: str | None) -> str:
        """Return the name of the data_point only name."""
        channel_parameter_name = self._get_channel_parameter_name(
            channel_name=channel_name, parameter_name=parameter_name
        )
        if device_name and channel_parameter_name and channel_parameter_name.startswith(device_name):
            return channel_parameter_name[len(device_name) :].lstrip()
        return channel_parameter_name


class HubNameData:
    """Class for hub data_point name parts."""

    __slots__ = (
        "full_name",
        "name",
    )

    def __init__(self, *, name: str, central_name: str | None = None, channel_name: str | None = None) -> None:
        """Init the DataPointNameData class."""
        self.name: Final = name
        self.full_name = (
            f"{channel_name} {self.name}".strip() if channel_name else f"{central_name} {self.name}".strip()
        )

    @staticmethod
    def empty() -> HubNameData:
        """Return an empty HubNameData."""
        return HubNameData(name="")


def check_length_and_log(name: str | None, value: Any) -> Any:
    """Check the length of a datapoint and log if too long."""
    if isinstance(value, str) and len(value) > 255:
        _LOGGER.debug(
            "Value of datapoint %s exceedes maximum allowed length of 255 chars. Value will be limited to 255 chars",
            name,
        )
        return value[0:255:1]
    return value


def get_device_name(central: hmcu.CentralUnit, device_address: str, model: str) -> str:
    """Return the cached name for a device, or an auto-generated."""
    if name := central.device_details.get_name(address=device_address):
        return name

    _LOGGER.debug(
        "GET_DEVICE_NAME: Using auto-generated name for %s %s",
        model,
        device_address,
    )
    return _get_generic_name(address=device_address, model=model)


def _get_generic_name(address: str, model: str) -> str:
    """Return auto-generated device/channel name."""
    return f"{model}_{address}"


def get_channel_name_data(channel: hmd.Channel) -> ChannelNameData:
    """Get name for data_point."""
    if channel_base_name := _get_base_name_from_channel_or_device(channel=channel):
        return ChannelNameData(
            device_name=channel.device.name,
            channel_name=channel_base_name,
        )

    _LOGGER.debug(
        "GET_CHANNEL_NAME_DATA: Using unique_id for %s %s",
        channel.device.model,
        channel.address,
    )
    return ChannelNameData.empty()


class PathData:
    """The data point path data."""

    @property
    @abstractmethod
    def set_path(self) -> str:
        """Return the base set path of the data_point."""

    @property
    @abstractmethod
    def state_path(self) -> str:
        """Return the base state path of the data_point."""


class DataPointPathData(PathData):
    """The data point path data."""

    __slots__ = (
        "_set_path",
        "_state_path",
    )

    def __init__(
        self,
        *,
        interface: Interface | None,
        address: str,
        channel_no: int | None,
        kind: str,
        name: str | None = None,
    ):
        """Init the path data."""
        path_item: Final = f"{address.upper()}/{channel_no}/{kind.upper()}"
        self._set_path: Final = (
            f"{VIRTDEV_SET_PATH_ROOT if interface == Interface.CCU_JACK else SET_PATH_ROOT}/{path_item}"
        )
        self._state_path: Final = (
            f"{VIRTDEV_STATE_PATH_ROOT if interface == Interface.CCU_JACK else STATE_PATH_ROOT}/{path_item}"
        )

    @property
    def set_path(self) -> str:
        """Return the base set path of the data_point."""
        return self._set_path

    @property
    def state_path(self) -> str:
        """Return the base state path of the data_point."""
        return self._state_path


class ProgramPathData(PathData):
    """The program path data."""

    __slots__ = (
        "_set_path",
        "_state_path",
    )

    def __init__(self, *, pid: str):
        """Init the path data."""
        self._set_path: Final = f"{PROGRAM_SET_PATH_ROOT}/{pid}"
        self._state_path: Final = f"{PROGRAM_STATE_PATH_ROOT}/{pid}"

    @property
    def set_path(self) -> str:
        """Return the base set path of the program."""
        return self._set_path

    @property
    def state_path(self) -> str:
        """Return the base state path of the program."""
        return self._state_path


class SysvarPathData(PathData):
    """The sysvar path data."""

    __slots__ = (
        "_set_path",
        "_state_path",
    )

    def __init__(self, *, vid: str):
        """Init the path data."""
        self._set_path: Final = f"{SYSVAR_SET_PATH_ROOT}/{vid}"
        self._state_path: Final = f"{SYSVAR_STATE_PATH_ROOT}/{vid}"

    @property
    def set_path(self) -> str:
        """Return the base set path of the sysvar."""
        return self._set_path

    @property
    def state_path(self) -> str:
        """Return the base state path of the sysvar."""
        return self._state_path


def get_data_point_name_data(
    channel: hmd.Channel,
    parameter: str,
) -> DataPointNameData:
    """Get name for data_point."""
    if channel_name := _get_base_name_from_channel_or_device(channel=channel):
        p_name = parameter.title().replace("_", " ")

        if _check_channel_name_with_channel_no(name=channel_name):
            c_name = channel_name.split(ADDRESS_SEPARATOR)[0]
            c_postfix = ""
            if channel.central.paramset_descriptions.is_in_multiple_channels(
                channel_address=channel.address, parameter=parameter
            ):
                c_postfix = "" if channel.no in (0, None) else f" ch{channel.no}"
            data_point_name = DataPointNameData(
                device_name=channel.device.name,
                channel_name=c_name,
                parameter_name=f"{p_name}{c_postfix}",
            )
        else:
            data_point_name = DataPointNameData(
                device_name=channel.device.name,
                channel_name=channel_name,
                parameter_name=p_name,
            )
        return data_point_name

    _LOGGER.debug(
        "GET_DATA_POINT_NAME: Using unique_id for %s %s %s",
        channel.device.model,
        channel.address,
        parameter,
    )
    return DataPointNameData.empty()


def get_hub_data_point_name_data(
    channel: hmd.Channel | None,
    legacy_name: str,
    central_name: str,
) -> HubNameData:
    """Get name for hub data_point."""
    if not channel:
        return HubNameData(
            central_name=central_name,
            name=legacy_name,
        )
    if channel_name := _get_base_name_from_channel_or_device(channel=channel):
        p_name = (
            legacy_name.replace("_", " ")
            .replace(channel.address, "")
            .replace(channel.id, "")
            .replace(channel.device.id, "")
            .strip()
        )

        if _check_channel_name_with_channel_no(name=channel_name):
            channel_name = channel_name.split(":")[0]

        return HubNameData(channel_name=channel_name, name=p_name)

    _LOGGER.debug(
        "GET_DATA_POINT_NAME: Using unique_id for %s %s %s",
        channel.device.model,
        channel.address,
        legacy_name,
    )
    return HubNameData.empty()


def get_event_name(
    channel: hmd.Channel,
    parameter: str,
) -> DataPointNameData:
    """Get name for event."""
    if channel_name := _get_base_name_from_channel_or_device(channel=channel):
        p_name = parameter.title().replace("_", " ")
        if _check_channel_name_with_channel_no(name=channel_name):
            c_name = "" if channel.no in (0, None) else f" ch{channel.no}"
            event_name = DataPointNameData(
                device_name=channel.device.name,
                channel_name=c_name,
                parameter_name=p_name,
            )
        else:
            event_name = DataPointNameData(
                device_name=channel.device.name,
                channel_name=channel_name,
                parameter_name=p_name,
            )
        return event_name

    _LOGGER.debug(
        "GET_EVENT_NAME: Using unique_id for %s %s %s",
        channel.device.model,
        channel.address,
        parameter,
    )
    return DataPointNameData.empty()


def get_custom_data_point_name(
    channel: hmd.Channel,
    is_only_primary_channel: bool,
    ignore_multiple_channels_for_name: bool,
    usage: DataPointUsage,
    postfix: str = "",
) -> DataPointNameData:
    """Get name for custom data_point."""
    if channel_name := _get_base_name_from_channel_or_device(channel=channel):
        if (is_only_primary_channel or ignore_multiple_channels_for_name) and _check_channel_name_with_channel_no(
            name=channel_name
        ):
            return DataPointNameData(
                device_name=channel.device.name,
                channel_name=channel_name.split(ADDRESS_SEPARATOR)[0],
                parameter_name=postfix,
            )
        if _check_channel_name_with_channel_no(name=channel_name):
            c_name = channel_name.split(ADDRESS_SEPARATOR)[0]
            p_name = channel_name.split(ADDRESS_SEPARATOR)[1]
            marker = "ch" if usage == DataPointUsage.CDP_PRIMARY else "vch"
            p_name = f"{marker}{p_name}"
            return DataPointNameData(device_name=channel.device.name, channel_name=c_name, parameter_name=p_name)
        return DataPointNameData(device_name=channel.device.name, channel_name=channel_name)

    _LOGGER.debug(
        "GET_CUSTOM_DATA_POINT_NAME: Using unique_id for %s %s %s",
        channel.device.model,
        channel.address,
        channel.no,
    )
    return DataPointNameData.empty()


def generate_unique_id(
    central: hmcu.CentralUnit,
    address: str,
    parameter: str | None = None,
    prefix: str | None = None,
) -> str:
    """
    Build unique identifier from address and parameter.

    Central id is additionally used for heating groups.
    Prefix is used for events and buttons.
    """
    unique_id = address.replace(ADDRESS_SEPARATOR, "_").replace("-", "_")
    if parameter:
        unique_id = f"{unique_id}_{parameter}"

    if prefix:
        unique_id = f"{prefix}_{unique_id}"
    if (
        address in (PROGRAM_ADDRESS, SYSVAR_ADDRESS)
        or address.startswith("INT000")
        or address.split(ADDRESS_SEPARATOR)[0] in VIRTUAL_REMOTE_ADDRESSES
    ):
        return f"{central.config.central_id}_{unique_id}".lower()
    return f"{unique_id}".lower()


def generate_channel_unique_id(
    central: hmcu.CentralUnit,
    address: str,
) -> str:
    """Build unique identifier for a channel from address."""
    unique_id = address.replace(ADDRESS_SEPARATOR, "_").replace("-", "_")
    if address.split(ADDRESS_SEPARATOR)[0] in VIRTUAL_REMOTE_ADDRESSES:
        return f"{central.config.central_id}_{unique_id}".lower()
    return unique_id.lower()


def _get_base_name_from_channel_or_device(channel: hmd.Channel) -> str | None:
    """Get the name from channel if it's not default, otherwise from device."""
    default_channel_name = f"{channel.device.model} {channel.address}"
    name = channel.central.device_details.get_name(address=channel.address)
    if name is None or name == default_channel_name:
        return channel.device.name if channel.no is None else f"{channel.device.name}:{channel.no}"
    return name


def _check_channel_name_with_channel_no(name: str) -> bool:
    """Check if name contains channel and this is an int."""
    if name.count(ADDRESS_SEPARATOR) == 1:
        channel_part = name.split(ADDRESS_SEPARATOR)[1]
        try:
            int(channel_part)
        except ValueError:
            return False
        return True
    return False


def convert_value(value: Any, target_type: ParameterType, value_list: tuple[str, ...] | None) -> Any:
    """
    Convert a value to target_type with safe memoization.

    To avoid redundant conversions across layers, we use an internal
    LRU-cached helper for hashable inputs. For unhashable inputs, we
    fall back to a direct conversion path.
    """
    # Normalize value_list to tuple to ensure hashability where possible
    norm_value_list: tuple[str, ...] | None = tuple(value_list) if isinstance(value_list, list) else value_list
    try:
        # This will be cached if all arguments are hashable
        return _convert_value_cached(value, target_type, norm_value_list)
    except TypeError:
        # Fallback non-cached path if any argument is unhashable
        return _convert_value_noncached(value, target_type, norm_value_list)


@lru_cache(maxsize=2048)
def _convert_value_cached(value: Any, target_type: ParameterType, value_list: tuple[str, ...] | None) -> Any:
    return _convert_value_noncached(value, target_type, value_list)


def _convert_value_noncached(value: Any, target_type: ParameterType, value_list: tuple[str, ...] | None) -> Any:
    if value is None:
        return None
    if target_type == ParameterType.BOOL:
        if value_list:
            # relevant for ENUMs retyped to a BOOL
            return _get_binary_sensor_value(value=value, value_list=value_list)
        if isinstance(value, str):
            return to_bool(value=value)
        return bool(value)
    if target_type == ParameterType.FLOAT:
        return float(value)
    if target_type == ParameterType.INTEGER:
        return int(float(value))
    if target_type == ParameterType.STRING:
        return str(value)
    return value


def is_binary_sensor(parameter_data: ParameterData) -> bool:
    """Check, if the sensor is a binary_sensor."""
    if parameter_data["TYPE"] == ParameterType.BOOL:
        return True
    if value_list := parameter_data.get("VALUE_LIST"):
        return tuple(value_list) in _BINARY_SENSOR_TRUE_VALUE_DICT_FOR_VALUE_LIST
    return False


def _get_binary_sensor_value(value: int, value_list: tuple[str, ...]) -> bool:
    """Return, the value of a binary_sensor."""
    try:
        str_value = value_list[value]
        if true_value := _BINARY_SENSOR_TRUE_VALUE_DICT_FOR_VALUE_LIST.get(value_list):
            return str_value == true_value
    except IndexError:
        pass
    return False


def check_channel_is_the_only_primary_channel(
    current_channel_no: int | None,
    device_def: Mapping[str, Any],
    device_has_multiple_channels: bool,
) -> bool:
    """Check if this channel is the only primary channel."""
    primary_channel: int = device_def[hmed.CDPD.PRIMARY_CHANNEL]
    return bool(primary_channel == current_channel_no and device_has_multiple_channels is False)


def get_value_from_value_list(value: SYSVAR_TYPE, value_list: tuple[str, ...] | list[str] | None) -> str | None:
    """Check if value is in value list."""
    if value is not None and isinstance(value, int) and value_list is not None and value < len(value_list):
        return value_list[int(value)]
    return None


def get_index_of_value_from_value_list(
    value: SYSVAR_TYPE, value_list: tuple[str, ...] | list[str] | None
) -> int | None:
    """Check if value is in value list."""
    if value is not None and isinstance(value, str | StrEnum) and value_list is not None and value in value_list:
        return value_list.index(value)

    return None
