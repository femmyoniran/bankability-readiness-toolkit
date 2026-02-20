"""
Formatting and calculation utilities.
"""


def format_currency(value, decimals=0):
    """Format a number as US currency."""
    if value is None:
        return "$0"
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.{decimals}f}B"
    elif abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"${value:,.{decimals}f}"
    else:
        return f"${value:,.{min(decimals, 2)}f}"


def format_percent(value, decimals=1):
    """Format a decimal as a percentage string."""
    if value is None:
        return "0%"
    return f"{value * 100:.{decimals}f}%"


def format_number(value, decimals=0):
    """Format a number with commas."""
    if value is None:
        return "0"
    return f"{value:,.{decimals}f}"


def safe_divide(numerator, denominator, default=0.0):
    """Divide with protection against division by zero."""
    if denominator is None or denominator == 0:
        return default
    return numerator / denominator


def annuity_payment(principal, rate, periods):
    """Calculate the fixed annual payment on an amortizing loan."""
    if rate == 0:
        return principal / periods if periods > 0 else 0
    return principal * (rate * (1 + rate) ** periods) / ((1 + rate) ** periods - 1)


def present_value(future_value, rate, periods):
    """Calculate present value of a future cash flow."""
    if rate < 0 or periods < 0:
        return future_value
    return future_value / (1 + rate) ** periods


def compound_growth(base_value, growth_rate, periods):
    """Calculate a value after compound growth."""
    return base_value * (1 + growth_rate) ** periods
