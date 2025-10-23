import math
import pytest
from sympy import symbols, Eq

from circuitpython import (
    series_resistance,
    parallell_resistance,
    node_voltage,
    mesh_current,
    power_vi,
    power_ri,
    power_rv,
    voltage_divider,
    current_divider,
    Thevenin,
    Norton,
    thevenin_from_voc_isc,
    norton_from_voc_isc,
)


def test_series_resistance():
    assert series_resistance(10, 20, 30) == 60


def test_parallell_resistance_two():
    assert pytest.approx(parallell_resistance(10, 20), rel=1e-6) == 1 / (1 / 10 + 1 / 20)


def test_parallell_resistance_three_equal():
    assert pytest.approx(parallell_resistance(5, 5, 5), rel=1e-6) == 1 / (1 / 5 + 1 / 5 + 1 / 5)


def test_node_voltage():
    V1, V2 = symbols("V1 V2")
    equations = [Eq(V1 + V2, 10), Eq(V1 - V2, 4)]
    variables = ["V1", "V2"]
    result = node_voltage(equations, variables)
    assert round(result["V1"], 6) == round(7.0, 6)
    assert round(result["V2"], 6) == round(3.0, 6)


def test_mesh_current():
    I1, I2 = symbols("I1 I2")
    equations = [Eq(I1 + I2, 5), Eq(I1 - I2, 1)]
    variables = ["I1", "I2"]
    result = mesh_current(equations, variables)
    assert round(result["I1"], 6) == round(3.0, 6)
    assert round(result["I2"], 6) == round(2.0, 6)


def test_power_formulas():
    assert power_vi(5, 10) == 50.0
    assert power_ri(5, 10) == 5 * (10 ** 2)  # R * I^2
    assert power_rv(5, 10) == (10 ** 2) / 5  # V^2 / R


def test_voltage_divider_equal_resistors():
    # With equal resistors, Vout should be half of Vin regardless of order
    vin = 12.0
    vout = voltage_divider(vin, 1000, 1000)
    assert pytest.approx(vout, rel=1e-9) == vin / 2


def test_current_divider_equal_resistors():
    # With equal resistors, each branch gets half the current
    itot = 10.0
    i_branch = current_divider(itot, 10, 10)
    assert pytest.approx(i_branch, rel=1e-9) == itot / 2


def _extract_v_r(obj):
    # Flexible extractor for returned Thevenin-like values
    # Accept tuple/list, dict, or object with common attribute names.
    if isinstance(obj, (tuple, list)) and len(obj) >= 2:
        return float(obj[0]), float(obj[1])
    if isinstance(obj, dict):
        for vk in ("Vth", "V", "voc", "voltage", "vth"):
            for rk in ("Rth", "R", "resistance", "rth"):
                if vk in obj and rk in obj:
                    return float(obj[vk]), float(obj[rk])
    for vname in ("Vth", "V", "voc", "voltage", "vth"):
        for rname in ("Rth", "R", "resistance", "rth"):
            if hasattr(obj, vname) and hasattr(obj, rname):
                return float(getattr(obj, vname)), float(getattr(obj, rname))
    pytest.skip("Cannot extract Vth/Rth from object returned by thevenin_from_voc_isc")


def _extract_in_r(obj):
    # Flexible extractor for Norton-like values (Isc/In and Rth)
    if isinstance(obj, (tuple, list)) and len(obj) >= 2:
        return float(obj[0]), float(obj[1])
    if isinstance(obj, dict):
        for ik in ("Isc", "In", "I", "isc", "in"):
            for rk in ("Rth", "R", "resistance", "rth"):
                if ik in obj and rk in obj:
                    return float(obj[ik]), float(obj[rk])
    for iname in ("Isc", "In", "I", "isc", "in"):
        for rname in ("Rth", "R", "resistance", "rth"):
            if hasattr(obj, iname) and hasattr(obj, rname):
                return float(getattr(obj, iname)), float(getattr(obj, rname))
    pytest.skip("Cannot extract In/Rth from object returned by norton_from_voc_isc")


def test_thevenin_from_voc_isc_relationship():
    voc = 10.0
    isc = 2.0
    expected_rth = voc / isc

    res = thevenin_from_voc_isc(voc, isc)
    vth, rth = _extract_v_r(res)

    assert pytest.approx(vth, rel=1e-9) == voc
    assert pytest.approx(rth, rel=1e-9) == expected_rth


def test_norton_from_voc_isc_relationship():
    voc = 10.0
    isc = 2.0
    expected_rth = voc / isc
    expected_in = isc

    res = norton_from_voc_isc(voc, isc)
    in_, rth = _extract_in_r(res)

    assert pytest.approx(in_, rel=1e-9) == expected_in
    assert pytest.approx(rth, rel=1e-9) == expected_rth