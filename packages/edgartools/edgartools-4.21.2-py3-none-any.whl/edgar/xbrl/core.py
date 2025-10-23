"""
Core utilities for XBRL processing.

This module provides common functions used throughout the XBRL parser.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# Constants for label roles
STANDARD_LABEL = "http://www.xbrl.org/2003/role/label"
TERSE_LABEL = "http://www.xbrl.org/2003/role/terseLabel"
PERIOD_START_LABEL = "http://www.xbrl.org/2003/role/periodStartLabel"
PERIOD_END_LABEL = "http://www.xbrl.org/2003/role/periodEndLabel"
TOTAL_LABEL = "http://www.xbrl.org/2003/role/totalLabel"

# XML namespaces
NAMESPACES = {
    "xlink": "http://www.w3.org/1999/xlink",
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "xbrli": "http://www.xbrl.org/2003/instance",
    "link": "http://www.xbrl.org/2003/linkbase"
}


def parse_date(date_str: str) -> datetime.date:
    """
    Parse an XBRL date string to a date object.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        datetime.date object
    """
    if not date_str:
        raise ValueError("Empty date string provided")

    try:
        # Parse the date string
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Additional validation - some dates in XBRL can have invalid day values
        # (e.g. September 31, which doesn't exist)
        year, month, day = map(int, date_str.split('-'))

        # Validate day of month
        if month == 2:  # February
            if day > 29:
                # February never has more than 29 days
                raise ValueError(f"Invalid day {day} for February")
            elif day == 29 and not (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
                # February 29 is only valid in leap years
                raise ValueError(f"Invalid day 29 for February in non-leap year {year}")
        elif month in [4, 6, 9, 11] and day > 30:
            # April, June, September, November have 30 days max
            raise ValueError(f"Invalid day {day} for month {month}")
        elif day > 31:
            # No month has more than 31 days
            raise ValueError(f"Invalid day {day}")

        return date_obj
    except (ValueError, TypeError) as e:
        # Provide more specific error message
        raise ValueError(f"Invalid date format or value: {date_str} - {str(e)}") from e


def format_date(date_obj: datetime.date) -> str:
    """
    Format a date object to a human-readable string.

    Args:
        date_obj: datetime.date object

    Returns:
        Formatted date string (e.g., "Sep 30, 2023")
    """
    # Use abbreviated month format (%b) instead of full month (%B)
    formatted_date = date_obj.strftime('%b %d, %Y')

    # Remove leading zeros from day
    if formatted_date.split()[1].startswith('0'):
        day_part = formatted_date.split()[1].lstrip('0')
        formatted_date = f"{formatted_date.split()[0]} {day_part} {formatted_date.split()[2]}"

    return formatted_date


def extract_element_id(href: str) -> str:
    """
    Extract element ID from an XLink href.

    Args:
        href: XLink href attribute value

    Returns:
        Element ID
    """
    return href.split('#')[-1]


def classify_duration(days: int) -> str:
    """
    Classify a duration in days as quarterly, semi-annual, annual, etc.

    Args:
        days: Duration in days

    Returns:
        Description of the duration (e.g., "Quarterly", "Annual")
    """
    if 85 <= days <= 95:
        return "Quarterly"
    elif 175 <= days <= 185:
        return "Semi-Annual"
    elif 265 <= days <= 285:
        return "Nine Months"
    elif 350 <= days <= 380:
        return "Annual"
    else:
        return "Period"


def determine_dominant_scale(statement_data: List[Dict[str, Any]], 
                             periods_to_display: List[Tuple[str, str]]) -> int:
    """
    Determine the dominant scale (thousands, millions, billions) for a statement.

    This looks at all monetary values in the statement and determines the most appropriate
    scale to use for the "In millions/billions/thousands" note.

    Args:
        statement_data: The statement data with items and values
        periods_to_display: List of period keys and labels to consider

    Returns:
        int: The dominant scale (-3 for thousands, -6 for millions, -9 for billions, 0 for no scaling)
    """
    # Collect all decimals attributes
    all_decimals = []
    for item in statement_data:
        # Skip non-monetary items or items without values
        if not item.get('has_values', False) or not item.get('values'):
            continue

        # Skip items that appear to be share counts or ratios
        label_lower = item['label'].lower()
        if any(keyword in label_lower for keyword in [
            'shares', 'share', 'stock', 'eps', 'earnings per share', 
            'weighted average', 'number of', 'per common share', 'per share',
            'per basic', 'per diluted', 'outstanding', 'issued',
            'ratio', 'margin', 'percentage', 'rate', 'per cent'
        ]):
            continue

        # Get all decimals values for this item
        for period_key, _ in periods_to_display:
            if period_key in item.get('decimals', {}):
                decimals = item['decimals'][period_key]
                if isinstance(decimals, int):
                    all_decimals.append(decimals)

    # If we have decimals information, use that to determine the scale
    if all_decimals:
        # Count the occurrences of each scale
        scale_counts = {
            -9: 0,  # billions
            -6: 0,  # millions
            -3: 0,  # thousands
            0: 0    # no scaling
        }

        for decimals in all_decimals:
            if decimals <= -9:
                scale_counts[-9] += 1
            elif decimals <= -6:
                scale_counts[-6] += 1
            elif decimals <= -3:
                scale_counts[-3] += 1
            else:
                scale_counts[0] += 1

        # Find the most common scale (excluding no scaling)
        most_common_scale = 0
        max_count = 0

        for scale, count in scale_counts.items():
            if scale != 0 and count > max_count:  # Prioritize scaling over no scaling
                max_count = count
                most_common_scale = scale

        return most_common_scale

    # If no decimals information, examine the magnitude of values
    all_values = []
    for item in statement_data:
        if not item.get('has_values', False) or not item.get('values'):
            continue

        # Skip items that appear to be share counts or ratios
        label_lower = item['label'].lower()
        if any(keyword in label_lower for keyword in [
            'shares', 'share', 'stock', 'eps', 'earnings per share', 
            'weighted average', 'number of', 'per common share', 'per share',
            'per basic', 'per diluted', 'outstanding', 'issued',
            'ratio', 'margin', 'percentage', 'rate', 'per cent'
        ]):
            continue

        # Get all values for this item
        for period_key, _ in periods_to_display:
            value = item['values'].get(period_key)
            if isinstance(value, (int, float)) and value != 0:
                all_values.append(abs(value))

    # Determine the appropriate scale based on the magnitude of values
    if all_values:
        # Calculate median value to avoid outliers affecting the scale
        all_values.sort()
        median_value = all_values[len(all_values) // 2]

        if median_value >= 1_000_000_000:
            return -9  # billions
        elif median_value >= 1_000_000:
            return -6  # millions
        elif median_value >= 1_000:
            return -3  # thousands

    # Default to millions if we couldn't determine a scale
    return -6


def get_currency_symbol(unit_measure: Optional[str]) -> str:
    """
    Get the appropriate currency symbol from a unit measure string.

    Args:
        unit_measure: Unit measure string (e.g., 'iso4217:USD', 'iso4217:EUR')

    Returns:
        Currency symbol (e.g., '$', '€', '£')
    """
    if not unit_measure:
        return "$"  # Default to USD

    # Map common ISO 4217 currency codes to symbols
    currency_symbols = {
        'iso4217:USD': '$',
        'iso4217:EUR': '€',
        'iso4217:GBP': '£',
        'iso4217:JPY': '¥',
        'iso4217:CAD': 'C$',
        'iso4217:AUD': 'A$',
        'iso4217:CHF': 'CHF',
        'iso4217:CNY': '¥',
        'iso4217:INR': '₹',
        'iso4217:KRW': '₩',
        'iso4217:BRL': 'R$',
        'iso4217:MXN': 'MX$',
        'iso4217:SEK': 'kr',
        'iso4217:NOK': 'kr',
        'iso4217:DKK': 'kr',
        'iso4217:PLN': 'zł',
        'iso4217:CZK': 'Kč',
        'iso4217:HUF': 'Ft',
        'iso4217:RUB': '₽',
        'iso4217:ZAR': 'R',
        'iso4217:SGD': 'S$',
        'iso4217:HKD': 'HK$',
        'iso4217:TWD': 'NT$',
        'iso4217:THB': '฿',
        'iso4217:MYR': 'RM',
        'iso4217:IDR': 'Rp',
        'iso4217:PHP': '₱',
        'iso4217:VND': '₫',
        'iso4217:ILS': '₪',
        'iso4217:TRY': '₺',
        'iso4217:AED': 'AED',
        'iso4217:SAR': 'SR',
        'iso4217:EGP': 'E£',
        'iso4217:NGN': '₦',
    }

    return currency_symbols.get(unit_measure, '$')  # Default to USD if unknown


def format_value(value: Union[int, float, str], is_monetary: bool, scale: int,
                 decimals: Optional[int] = None, currency_symbol: Optional[str] = None) -> str:
    """
    Format a value with appropriate scaling and formatting.

    Args:
        value: The value to format
        is_monetary: Whether the value is monetary
        scale: The scale to apply (-3 for thousands, -6 for millions, -9 for billions)
        decimals: XBRL decimals attribute value (optional)
        currency_symbol: Currency symbol to use for monetary values (default: '$')

    Returns:
        Formatted value string
    """
    # Handle non-numeric or zero values
    if not isinstance(value, (int, float)) or value == 0:
        return "" if value == 0 else str(value)

    # Apply scaling
    scaled_value = value
    if scale <= -9:  # Billions
        scaled_value = value / 1_000_000_000
    elif scale <= -6:  # Millions
        scaled_value = value / 1_000_000
    elif scale <= -3:  # Thousands
        scaled_value = value / 1_000

    # Determine decimal places to show
    if isinstance(decimals, int):
        if decimals >= 0:
            # Positive decimals - show up to 2 decimal places
            decimal_places = min(2, decimals)
        else:
            # For negative decimals, adjust based on scaling
            if scale <= -9:  # Billions
                decimal_places = min(2, max(0, decimals + 9))
            elif scale <= -6:  # Millions
                decimal_places = min(2, max(0, decimals + 6))
            elif scale <= -3:  # Thousands
                decimal_places = min(2, max(0, decimals + 3))
            else:
                # For unscaled values, respect the decimals attribute
                # If decimals is negative, show that many zeros to the left of decimal
                # E.g., decimals=-2 means precision to hundreds place (two zeros after decimal)
                decimal_places = max(0, -decimals)
    else:
        # Default decimal places
        if is_monetary:
            decimal_places = 0  # Standard for financial statements
        else:
            # For non-monetary values, check if it's effectively a whole number
            if abs(round(value) - value) < 0.001:
                decimal_places = 0  # Effectively whole numbers
            else:
                decimal_places = 2  # Show 2 decimals for actual fractional values

    # Apply formatting
    decimal_format = f",.{decimal_places}f"

    # Format with currency symbol if monetary, otherwise just format the number
    if is_monetary:
        # Use the provided currency symbol or default to '$'
        symbol = currency_symbol if currency_symbol is not None else '$'
        if value < 0:
            return f"{symbol}({abs(scaled_value):{decimal_format}})"
        else:
            return f"{symbol}{scaled_value:{decimal_format}}"
    else:
        # For non-monetary values, use parentheses for negative numbers
        if value < 0:
            return f"({abs(scaled_value):{decimal_format}})"
        else:
            return f"{scaled_value:{decimal_format}}"


def find_previous_fiscal_year_period(instant_periods: List[Dict[str, Any]],
                                    prev_fiscal_year: int,
                                    fiscal_month: int,
                                    fiscal_day: int) -> Optional[Dict[str, Any]]:
    """
    Find the previous fiscal year period using simple matching logic.

    Args:
        instant_periods: List of instant periods sorted by date (most recent first)
        prev_fiscal_year: Previous fiscal year to find
        fiscal_month: Fiscal year end month
        fiscal_day: Fiscal year end day

    Returns:
        Previous fiscal year period or None if not found
    """
    for period in instant_periods[1:]:  # Skip the current one
        try:
            period_date = parse_date(period['date'])
            # Check if this period is from the previous fiscal year and around fiscal year end
            if (period_date.year == prev_fiscal_year and
                period_date.month == fiscal_month and
                abs(period_date.day - fiscal_day) <= 7):
                return period
        except (ValueError, TypeError):
            continue
    return None


def get_unit_display_name(unit_ref: Optional[str]) -> Optional[str]:
    """
    Convert unit_ref to human-readable unit name.

    Maps XBRL unit references to standard display names:
    - 'U-Monetary' / 'iso4217:USD' -> 'usd'
    - 'U-Shares' / 'shares' -> 'shares'
    - 'U-USD-per-shares' -> 'usdPerShare'
    - etc.

    Args:
        unit_ref: XBRL unit reference string

    Returns:
        Human-readable unit name or None if unit_ref is None

    Examples:
        >>> get_unit_display_name('U-Monetary')
        'usd'
        >>> get_unit_display_name('U-Shares')
        'shares'
        >>> get_unit_display_name('U-USD-per-shares')
        'usdPerShare'
    """
    if not unit_ref:
        return None

    # Common unit patterns and their standard names
    unit_ref_lower = unit_ref.lower()

    # Per-share units (ratios) - Check FIRST before simple monetary/share checks
    if 'per' in unit_ref_lower and 'share' in unit_ref_lower:
        if 'usd' in unit_ref_lower or 'monetary' in unit_ref_lower:
            return 'usdPerShare'
        elif 'eur' in unit_ref_lower:
            return 'eurPerShare'
        elif 'gbp' in unit_ref_lower:
            return 'gbpPerShare'
        else:
            return 'perShare'

    # Share units (but not per-share)
    if 'share' in unit_ref_lower:
        return 'shares'

    # Monetary units
    if 'monetary' in unit_ref_lower or 'iso4217:usd' in unit_ref_lower or unit_ref_lower == 'usd':
        return 'usd'
    elif 'eur' in unit_ref_lower or 'iso4217:eur' in unit_ref_lower:
        return 'eur'
    elif 'gbp' in unit_ref_lower or 'iso4217:gbp' in unit_ref_lower:
        return 'gbp'
    elif 'jpy' in unit_ref_lower or 'iso4217:jpy' in unit_ref_lower:
        return 'jpy'

    # Pure numbers / ratios (no unit)
    if 'pure' in unit_ref_lower or 'number' in unit_ref_lower:
        return 'number'

    # Default: return a simplified version of the unit_ref
    # Remove common prefixes and normalize
    simplified = unit_ref.replace('U-', '').replace('iso4217:', '')
    return simplified.lower()


def is_point_in_time(period_type: Optional[str]) -> Optional[bool]:
    """
    Determine if a period type represents a point-in-time value.

    Args:
        period_type: XBRL period type ('instant' or 'duration')

    Returns:
        True for 'instant' periods, False for 'duration' periods, None if period_type is None

    Examples:
        >>> is_point_in_time('instant')
        True
        >>> is_point_in_time('duration')
        False
        >>> is_point_in_time(None)
        None
    """
    if period_type is None:
        return None
    return period_type == 'instant'
