"""
Financial arithmetic utilities using Decimal for authoritative precision.
Prevents IEEE-754 binary floating-point roundoff errors in financial records.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional, Tuple, List, Dict, Any

CENT = Decimal('0.01')


def to_decimal(val: Union[float, int, str, Decimal, None], default: str = '0.00') -> Decimal:
    """Convert any monetary value to a quantized Decimal (2 decimal places)."""
    if val is None or val == '':
        return Decimal(default).quantize(CENT, rounding=ROUND_HALF_UP)
    try:
        if isinstance(val, (int, str)):
            d = Decimal(str(val).strip().replace(',', ''))
        elif isinstance(val, float):
            d = Decimal(f"{val:.6f}")
        elif isinstance(val, Decimal):
            d = val
        else:
            d = Decimal(str(val))
        return d.quantize(CENT, rounding=ROUND_HALF_UP)
    except Exception:
        return Decimal(default).quantize(CENT, rounding=ROUND_HALF_UP)


def to_float(val: Union[Decimal, float, int, str, None]) -> float:
    """Safely convert Decimal or other monetary representation to float for JSON output."""
    return float(to_decimal(val))


def to_cents(val: Union[Decimal, float, int, str, None]) -> int:
    """Convert monetary amount to integer cents."""
    d = to_decimal(val)
    return int((d * 100).to_integral_value(rounding=ROUND_HALF_UP))


def from_cents(cents: int) -> Decimal:
    """Convert integer cents back to Decimal."""
    return (Decimal(cents) / Decimal(100)).quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_line_item_total(quantity: Union[Decimal, float, int], unit_price: Union[Decimal, float, int]) -> Decimal:
    """Calculate line item total: quantity * unit_price rounded to nearest cent."""
    q = Decimal(str(quantity)) if not isinstance(quantity, Decimal) else quantity
    p = to_decimal(unit_price)
    return (q * p).quantize(CENT, rounding=ROUND_HALF_UP)


def verify_financial_equation(
    subtotal: Union[Decimal, float],
    tax_amount: Union[Decimal, float],
    discount: Union[Decimal, float],
    total: Union[Decimal, float],
    tolerance: Decimal = Decimal('0.05')
) -> Tuple[bool, Decimal, str]:
    """
    Verify subtotal + tax_amount - discount == total within permissible rounding tolerance.
    Returns (is_consistent, computed_total, error_message_if_any).
    """
    sub = to_decimal(subtotal)
    tax = to_decimal(tax_amount)
    disc = to_decimal(discount)
    tot = to_decimal(total)

    expected = (sub + tax - disc).quantize(CENT, rounding=ROUND_HALF_UP)
    diff = abs(expected - tot)

    if diff <= tolerance:
        return True, expected, ""
    else:
        return (
            False,
            expected,
            f"Total inconsistency: subtotal ({sub}) + tax ({tax}) - discount ({disc}) = {expected}, but stated total is {tot} (discrepancy: {diff})"
        )
