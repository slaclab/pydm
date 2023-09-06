from typing import Any
import pytest

from pytestqt.qtbot import QtBot
from qtpy.QtCore import Signal, QObject
import numpy as np

from pydm.application import PyDMApplication
from pydm.data_plugins.calc_plugin import epics_string, epics_unsigned
from pydm.widgets.channel import PyDMChannel


@pytest.mark.parametrize(
    "input_string,expected",
    [
        (np.array((0x6F, 0x6B, 0x61, 0x79, 0, 42), dtype=np.int8), "okay"),
        (np.array((0x6F, 0x6B, 0x61, 0x79), dtype=np.int8), "okay"),
        (np.array((0, 0x6F, 0x6B, 0x61, 0x79, 0, 42, 42), dtype=np.int8), ""),
    ],
)
def test_epics_string(input_string: str, expected: str):
    assert epics_string(input_string) == expected


@pytest.mark.parametrize(
    "input_int,bits,expected",
    [
        (100, 32, 100),
        (-1, 8, 255),
        (-2, 4, 0b1110),
    ],
)
def test_epics_unsigned(input_int: int, bits: int, expected: int):
    assert epics_unsigned(input_int, bits) == expected


@pytest.mark.parametrize(
    "calc,input1,expected1,input2,expected2",
    [
        ("val + 3", 0, 3, 1, 4),
        ("int(np.abs(val))", -5, 5, -10, 10),
        ("math.floor(val)", 3.4, 3, 5.7, 5),
        ("epics_string(val)", np.array((0x61, 0), dtype=np.int8), "a", np.array((0x62, 0), dtype=np.int8), "b"),
        ("epics_unsigned(val, 8)", -1, 255, -2, 254),
    ],
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
    class SigHolder(QObject):
        sig = Signal(type(input1))

    sig_holder = SigHolder()
    type_str = str(type(input1))
    local_addr = f"loc://test_calc_plugin_local_{calc}"
    local_ch = PyDMChannel(
        address=f"{local_addr}?type={type_str}&init={input1}",
        value_signal=sig_holder.sig,
    )
    local_ch.connect()
    calc_values = []

    def new_calc_value(val: Any):
        calc_values.append(val)

    calc_addr = f"calc://test_calc_plugin_calc_{calc}"
    calc_ch = PyDMChannel(
        address=f"{calc_addr}?val={local_addr}&expr={calc}",
        value_slot=new_calc_value,
    )
    calc_ch.connect()
    sig_holder.sig.emit(input1)

    def has_value():
        assert len(calc_values) >= 1

    qtbot.wait_until(has_value)
    assert calc_values[0] == expected1
    calc_values.clear()
    sig_holder.sig.emit(input2)
    qtbot.wait_until(has_value)
    assert calc_values[0] == expected2
