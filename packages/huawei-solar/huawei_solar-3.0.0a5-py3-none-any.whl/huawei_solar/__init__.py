"""Interact with Huawei inverters over Modbus."""

from huawei_solar.device import (
    EMMADevice,
    HuaweiSolarDevice,
    HuaweiSolarDeviceWithLogin,
    SChargerDevice,
    SDongleDevice,
    SmartLoggerDevice,
    SUN2000Device,
    create_device_instance,
    create_sub_device_instance,
)
from huawei_solar.device_discovery import DeviceIdentifier, DeviceInfo, get_device_identifiers, get_device_infos

from .exceptions import (
    ConnectionException,
    ConnectionInterruptedException,
    DecodeError,
    EncodeError,
    HuaweiSolarException,
    InvalidCredentials,
    PeakPeriodsValidationError,
    ReadException,
    TimeOfUsePeriodsException,
    WriteException,
)
from .modbus_client import AsyncHuaweiSolarClient, create_rtu_client, create_tcp_client
from .register_definitions import Result
from .register_names import RegisterName

__all__ = [
    "AsyncHuaweiSolarClient",
    "ConnectionException",
    "ConnectionInterruptedException",
    "DecodeError",
    "DeviceIdentifier",
    "DeviceInfo",
    "EMMADevice",
    "EncodeError",
    "HuaweiSolarDevice",
    "HuaweiSolarDeviceWithLogin",
    "HuaweiSolarException",
    "InvalidCredentials",
    "PeakPeriodsValidationError",
    "ReadException",
    "RegisterName",
    "Result",
    "SChargerDevice",
    "SDongleDevice",
    "SUN2000Device",
    "SmartLoggerDevice",
    "TimeOfUsePeriodsException",
    "WriteException",
    "create_device_instance",
    "create_rtu_client",
    "create_sub_device_instance",
    "create_tcp_client",
    "get_device_identifiers",
    "get_device_infos",
]
