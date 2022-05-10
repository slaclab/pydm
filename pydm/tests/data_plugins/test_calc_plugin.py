from typing import Any
import pytest

from pytestqt.qtbot import QtBot
from qtpy.QtCore import Signal
import numpy as np

from pydm.application import PyDMApplication
from pydm.data_plugins.calc_plugin import epics_string, epics_unsigned
from pydm.widgets.channel import PyDMChannel


@pytest.mark.parametrize(
    "input_string,expected",
    [
        (np.array((0x6f, 0x6b, 0x61, 0x79, 0, 42), dtype=np.int8), "okay"),
        (np.array((0x6f, 0x6b, 0x61, 0x79), dtype=np.int8), "okay"),
        (np.array((0, 0x6f, 0x6b, 0x61, 0x79, 0, 42, 42), dtype=np.int8), ""),
    ],
)
def test_epics_string(input_string: str, expected: str):
    assert epics_string(input_string) == expected


@pytest.mark.parametrize(
    "input_int,bits,expected",
    [
        (100, 32, 100),
        (-1, 8, 129),
        (-0b111, 4, 0b1111),
    ],
)
def test_epics_unsigned(input_int: int, bits: int, expected: int):
    assert epics_unsigned(input_int, bits, expected)


@pytest.mark.parametrize(
    "calc,input1,expected1,input2,expected2",
    [
        ('val + 3', 0, 3, 1, 4),
        ('np.abs(val)', -5, 5, -10, 10),
        ('math.floor(val)', 3.4, 3, 5.7, 5),
        ('epics_string(val)',
         np.array((0x61, 0), dtype=np.int8), 'a',
         np.array((0x62, 0), dtype=np.int8), 'b'),
        ('epics_unsigned(val, 8)', -1, 256, -2, 255),
    ]
)
def test_calc_plugin(
    qapp: PyDMApplication,
    qtbot: QtBot,
    calc: str,
    input1: Any,
    expected1: Any,
    input2: Any,
    expected2: Any,
):
    sig = Signal(type(input1))
    type_str = str(type(input1))
    local_addr = f'local://test_calc_plugin_local_{calc}'
    local_ch = PyDMChannel(
        address=f'{local_addr}?type={type_str}&init={input1}',
        value_signal=sig,
    )
    local_ch.connect()
    calc_values = []

    def new_calc_value(val: Any):
        calc_values.append(val)

    calc_addr = f'calc://test_calc_plugin_calc_{calc}'
    calc_ch = PyDMChannel(
        address=f'{calc_addr}?var={local_addr}&expr={calc}',
        value_slot=new_calc_value,
    )
    calc_ch.connect()

    def has_first_value():
        assert len(calc_values) == 1

    qtbot.wait_until(has_first_value)
    sig.emit(input2)

    def has_second_value():
        assert len(calc_values) == 2

    qtbot.wait_until(has_second_value)
    assert calc_values[0] == expected1
    assert calc_values[1] == expected2
