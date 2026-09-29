from decimal import Decimal
import pytest
from representations import exact_total, utc_timestamp


def test_exact_decimal_variation_without_float_construction():
    assert exact_total("0.10", 3) == Decimal("0.30")
    assert exact_total("12.34", 0) == Decimal("0.00")
    for price, quantity in [(0.5, 1), ("NaN", 1), ("Infinity", 1), ("-1", 1), ("0.001", 1), ("1", True), ("1", -1)]:
        with pytest.raises(ValueError):
            exact_total(price, quantity)


def test_utc_variation_requires_offset():
    assert utc_timestamp("2026-09-28T16:30:00+08:00") == "2026-09-28T08:30:00+00:00"
    with pytest.raises(ValueError):
        utc_timestamp("2026-09-28T08:30:00")
