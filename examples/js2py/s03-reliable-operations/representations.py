"""Data representation exercise: no floats masquerading as exact invoice amounts."""
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from uuid import UUID


def utc_timestamp(text: str) -> str:
    value = datetime.fromisoformat(text)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Offset required")
    return value.astimezone(UTC).isoformat()


def exact_total(unit_price: str, quantity: int) -> Decimal:
    # Independent variation only: the task API has no money fields or NUMERIC migration.
    if type(unit_price) is not str:
        raise ValueError("Price must be a decimal string, not float")
    if type(quantity) is not int or quantity < 0:
        raise ValueError("Nonnegative integer quantity required")
    try:
        price = Decimal(unit_price)
    except InvalidOperation:
        raise ValueError("Decimal string required") from None
    if not price.is_finite() or price < 0 or price.as_tuple().exponent < -2:
        raise ValueError("Finite nonnegative price with at most two fractional digits required")
    if price > Decimal("1000000") or quantity > 1000000:
        raise ValueError("Exercise bound exceeded")
    with localcontext() as context:
        context.prec = 28
        return (price * quantity).quantize(Decimal("0.01"))


if __name__ == "__main__":
    print(utc_timestamp("2026-09-28T16:30:00+08:00"))
    print(UUID("123e4567-e89b-42d3-a456-426614174000").version)
    print(exact_total("0.10", 3))
