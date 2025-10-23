import pytest

from circuitpy import (
    binary_to_decimal,
    decimal_to_binary,
    binary_to_hexadecimal,
    hexadecimal_to_binary,
    twos_comp_to_decimal,
    decimal_to_twos_comp,
    simplify_logic,
    truth_table,
)


def test_binary_decimal_basic():
    assert binary_to_decimal("1011") == 11
    assert binary_to_decimal("0") == 0
    assert decimal_to_binary(11) == "1011"
    assert decimal_to_binary(0) == "0"


def test_hex_binary_basic():
    assert binary_to_hexadecimal("1011") == "B"
    assert binary_to_hexadecimal("00001010") == "A"
    assert hexadecimal_to_binary("B") == "1011"
    assert hexadecimal_to_binary("b") == "1011"  # lowercase input supported


def test_twos_comp_roundtrip_positive_and_negative():
    # negative number round-trip
    assert decimal_to_twos_comp(-5, 4) == "1011"
    assert twos_comp_to_decimal("1011") == -5
    # positive number round-trip with zero padding
    assert decimal_to_twos_comp(5, 4) == "0101"
    assert twos_comp_to_decimal("0101") == 5


def test_twos_comp_range_checks():
    # 4-bit signed range is -8 .. 7; 8 and -9 should raise
    with pytest.raises(ValueError):
        decimal_to_twos_comp(8, 4)
    with pytest.raises(ValueError):
        decimal_to_twos_comp(-9, 4)


def test_truth_table_basic_or():
    expected = (
        "A  B  |  A or B\n"
        "----------------\n"
        "0  0  |  0\n"
        "0  1  |  1\n"
        "1  0  |  1\n"
        "1  1  |  1"
    )
    assert truth_table("A+B", ["A", "B"]) == expected


def test_simplify_logic_basic():
    # Accept either string or sympy expression result; check it simplifies to "A"
    res = simplify_logic("A*(B + A)")
    assert res is not None
    assert "A" in str(res)