"""Tests for time-of-use period register validation and encoding/decoding."""

import struct
from unittest.mock import MagicMock

import huawei_solar.register_names as rn
import pytest
from huawei_solar.exceptions import TimeOfUsePeriodsException
from huawei_solar.register_definitions.periods import (
    ChargeFlag,
    HUAWEI_LUNA2000_TimeOfUsePeriod,
    LG_RESU_TimeOfUsePeriod,
)
from huawei_solar.registers import REGISTERS

huawei_ppr = REGISTERS[rn.STORAGE_HUAWEI_LUNA2000_TIME_OF_USE_CHARGING_AND_DISCHARGING_PERIODS]
lg_ppr = REGISTERS[rn.STORAGE_LG_RESU_TIME_OF_USE_PRICE_PERIODS]


def test__validate__tou_periods__HUAWEI_LUNA2000__too_long_span__start_time() -> None:
    tou = HUAWEI_LUNA2000_TimeOfUsePeriod(
        start_time=60 * 24 + 1,
        end_time=15,
        charge_flag=ChargeFlag.DISCHARGE,
        days_effective=(True, True, True, True, True, True, True),
    )
    with pytest.raises(
        expected_exception=TimeOfUsePeriodsException,
        match=r"TOU period is invalid \(Spans over more than one day\)",
    ):
        huawei_ppr._validate([tou])


def test__validate__tou_periods__HUAWEI_LUNA2000__too_long_span__end_time() -> None:
    tou = HUAWEI_LUNA2000_TimeOfUsePeriod(
        start_time=15,
        end_time=60 * 24 + 1,
        charge_flag=ChargeFlag.DISCHARGE,
        days_effective=(True, True, True, True, True, True, True),
    )
    with pytest.raises(
        expected_exception=TimeOfUsePeriodsException,
        match=r"TOU period is invalid \(Spans over more than one day\)",
    ):
        huawei_ppr._validate([tou])


def test__validate__tou_periods__HUAWEI_LUNA2000__negative__start_time() -> None:
    tou = HUAWEI_LUNA2000_TimeOfUsePeriod(
        start_time=-10,
        end_time=15,
        charge_flag=ChargeFlag.DISCHARGE,
        days_effective=(True, True, True, True, True, True, True),
    )
    with pytest.raises(
        expected_exception=TimeOfUsePeriodsException,
        match=r"TOU period is invalid \(Below zero\)",
    ):
        huawei_ppr._validate([tou])


def test__validate__tou_periods__HUAWEI_LUNA2000__negative__end_time() -> None:
    tou = HUAWEI_LUNA2000_TimeOfUsePeriod(
        start_time=15,
        end_time=-2,
        charge_flag=ChargeFlag.DISCHARGE,
        days_effective=(True, True, True, True, True, True, True),
    )
    with pytest.raises(
        expected_exception=TimeOfUsePeriodsException,
        match=r"TOU period is invalid \(Below zero\)",
    ):
        huawei_ppr._validate([tou])


def test__validate__tou_periods__HUAWEI_LUNA2000__start_time_bigger_than_end_time() -> None:
    tou = HUAWEI_LUNA2000_TimeOfUsePeriod(
        start_time=15,
        end_time=2,
        charge_flag=ChargeFlag.DISCHARGE,
        days_effective=(True, True, True, True, True, True, True),
    )
    with pytest.raises(
        expected_exception=TimeOfUsePeriodsException,
        match=r"TOU period is invalid \(start-time is greater than end-time\)",
    ):
        huawei_ppr._validate([tou])


def test__validate__tou_periods__HUAWEI_LUNA2000__overlapping__1() -> None:
    tou = [
        HUAWEI_LUNA2000_TimeOfUsePeriod(
            start_time=120,
            end_time=160,
            charge_flag=ChargeFlag.DISCHARGE,
            days_effective=(True, True, True, True, True, True, True),
        ),
        HUAWEI_LUNA2000_TimeOfUsePeriod(
            start_time=100,
            end_time=150,
            charge_flag=ChargeFlag.DISCHARGE,
            days_effective=(True, True, True, True, True, True, True),
        ),
    ]
    with pytest.raises(
        expected_exception=TimeOfUsePeriodsException,
        match="TOU periods are overlapping",
    ):
        huawei_ppr._validate(tou)


def test__validate__tou_periods__HUAWEI_LUNA2000__overlapping__2() -> None:
    tou = [
        HUAWEI_LUNA2000_TimeOfUsePeriod(
            start_time=15,
            end_time=120,
            charge_flag=ChargeFlag.DISCHARGE,
            days_effective=(True, True, True, True, True, True, True),
        ),
        HUAWEI_LUNA2000_TimeOfUsePeriod(
            start_time=100,
            end_time=150,
            charge_flag=ChargeFlag.DISCHARGE,
            days_effective=(True, True, True, True, True, True, True),
        ),
    ]
    with pytest.raises(
        expected_exception=TimeOfUsePeriodsException,
        match="TOU periods are overlapping",
    ):
        huawei_ppr._validate(tou)


def test__validate__tou_periods__HUAWEI_LUNA2000__OK() -> None:
    tou = [
        HUAWEI_LUNA2000_TimeOfUsePeriod(
            start_time=15,
            end_time=120,
            charge_flag=ChargeFlag.DISCHARGE,
            days_effective=(True, True, True, True, True, True, True),
        ),
        HUAWEI_LUNA2000_TimeOfUsePeriod(
            start_time=121,
            end_time=150,
            charge_flag=ChargeFlag.CHARGE,
            days_effective=(False, True, True, True, True, True, True),
        ),
    ]
    huawei_ppr._validate(tou)

    encoded = huawei_ppr.encode(tou)

    encoded_bytes = struct.pack(f">{huawei_ppr.format}", *encoded)

    assert len(encoded_bytes) == huawei_ppr.length * 2
    validation_bytes = struct.pack(
        ">43H",
        *[
            2,
            15,
            120,
            383,
            121,
            150,
            126,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
    )

    assert encoded_bytes == validation_bytes


def test__validate__tou_periods__HUAWEI_LUNA2000__OK_2() -> None:
    tou = [
        HUAWEI_LUNA2000_TimeOfUsePeriod(
            start_time=15,
            end_time=120,
            charge_flag=ChargeFlag.DISCHARGE,
            days_effective=(True, True, True, True, True, True, True),
        ),
        HUAWEI_LUNA2000_TimeOfUsePeriod(
            start_time=0,
            end_time=14,
            charge_flag=ChargeFlag.DISCHARGE,
            days_effective=(True, True, True, True, True, True, True),
        ),
    ]
    huawei_ppr._validate(tou)
    encoded = huawei_ppr.encode(tou)
    encoded_bytes = struct.pack(f">{huawei_ppr.format}", *encoded)
    assert encoded_bytes == struct.pack(
        ">43H",
        *[
            2,
            15,
            120,
            383,
            0,
            14,
            383,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
    )

    decoded = huawei_ppr.decode(encoded).value

    assert decoded == tou


def test__validate__tou_periods__HUAWEI_LUNA2000__OK__different_days() -> None:
    tou = [
        HUAWEI_LUNA2000_TimeOfUsePeriod(
            start_time=0,
            end_time=120,
            charge_flag=ChargeFlag.DISCHARGE,
            days_effective=(False, False, False, True, True, False, True),
        ),
        HUAWEI_LUNA2000_TimeOfUsePeriod(
            start_time=0,
            end_time=120,
            charge_flag=ChargeFlag.DISCHARGE,
            days_effective=(True, False, True, False, False, True, False),
        ),
    ]

    huawei_ppr._validate(tou)
    encoded = huawei_ppr.encode(tou)
    encoded_bytes = struct.pack(f">{huawei_ppr.format}", *encoded)

    assert encoded_bytes == struct.pack(
        ">43H",
        *[
            2,
            0,
            120,
            344,
            0,
            120,
            293,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
    )

    decoded = huawei_ppr.decode(encoded).value
    assert decoded == tou


def test__validate__tou_periodsG__RESU___OK() -> None:
    tou = [
        LG_RESU_TimeOfUsePeriod(start_time=5, end_time=15, electricity_price=1),
        LG_RESU_TimeOfUsePeriod(start_time=16, end_time=20, electricity_price=1),
    ]
    lg_ppr._validate(tou)
    encoded = lg_ppr.encode(tou)
    encoded_bytes = struct.pack(f">{lg_ppr.format}", *encoded)

    validation_bytes = struct.pack(
        ">41H",
        *[
            2,
            5,
            15,
            0,
            1000,
            16,
            20,
            0,
            1000,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ],
    )

    assert encoded_bytes == validation_bytes

    decoded = lg_ppr.decode(encoded).value
    assert decoded == tou


def test__validate__tou_periodsG__RESU___overlaping() -> None:
    tou = [
        LG_RESU_TimeOfUsePeriod(start_time=5, end_time=15, electricity_price=1),
        LG_RESU_TimeOfUsePeriod(start_time=5, end_time=15, electricity_price=1),
    ]
    with pytest.raises(
        expected_exception=TimeOfUsePeriodsException,
        match="TOU periods are overlapping",
    ):
        lg_ppr._validate(tou)


def test__validate__tou_periods__unknown_type() -> None:
    mock = MagicMock()
    mock.start_time = 10
    mock.end_time = 20
    tou = [mock]
    with pytest.raises(
        expected_exception=TimeOfUsePeriodsException,
        match="TOU period is of an unexpected type",
    ):
        huawei_ppr._validate(tou)


def test__validate__data_type__none() -> None:
    huawei_ppr._validate([])

    encoded = huawei_ppr.encode([])
    encoded_bytes = struct.pack(f">{huawei_ppr.format}", *encoded)

    assert encoded_bytes == b"\x00\x00" * huawei_ppr.length
