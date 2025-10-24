"""Date and duration parsing utilities for TaskRepo."""

import re
from datetime import datetime, timedelta
from typing import Union

from dateutil import parser as dateutil_parser

from taskrepo.utils.duration import parse_duration


def parse_date_or_duration(input_str: str) -> tuple[Union[datetime, timedelta], bool]:
    """Parse date or duration string to either datetime or timedelta.

    Supports multiple formats:
    - Durations: "1w", "2d", "3m", "1y" (returns timedelta, False)
    - Day keywords: "today", "tomorrow", "yesterday" (returns datetime, True)
    - Relative keywords: "next week", "next month", "next year" (returns datetime, True)
    - ISO dates: "2025-10-30" (returns datetime, True)
    - Natural dates: "Oct 30", "October 30 2025" (returns datetime, True)

    Args:
        input_str: Date or duration string to parse

    Returns:
        Tuple of (parsed_value, is_absolute_date)
        - If is_absolute_date is True, parsed_value is a datetime
        - If is_absolute_date is False, parsed_value is a timedelta

    Raises:
        ValueError: If format cannot be parsed

    Examples:
        >>> parse_date_or_duration("1w")
        (datetime.timedelta(days=7), False)
        >>> parse_date_or_duration("tomorrow")
        (datetime(2025, 10, 24, 0, 0), True)
        >>> parse_date_or_duration("2025-10-30")
        (datetime(2025, 10, 30, 0, 0), True)
    """
    input_str = input_str.strip().lower()

    # Try duration format first (1w, 2d, etc.)
    duration_pattern = r"^(\d+)(d|w|m|y)$"
    if re.match(duration_pattern, input_str):
        try:
            duration = parse_duration(input_str)
            return (duration, False)
        except ValueError:
            pass  # Fall through to other parsers

    # Handle day keywords
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)

    if input_str == "today":
        return (today, True)
    elif input_str == "tomorrow":
        return (today + timedelta(days=1), True)
    elif input_str == "yesterday":
        return (today - timedelta(days=1), True)

    # Handle relative keywords
    if input_str == "next week":
        return (today + timedelta(weeks=1), True)
    elif input_str == "next month":
        # Approximate: add 30 days
        return (today + timedelta(days=30), True)
    elif input_str == "next year":
        # Approximate: add 365 days
        return (today + timedelta(days=365), True)

    # Try ISO date format (YYYY-MM-DD)
    iso_date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    if re.match(iso_date_pattern, input_str):
        try:
            parsed = datetime.strptime(input_str, "%Y-%m-%d")
            return (parsed, True)
        except ValueError as e:
            raise ValueError(f"Invalid ISO date format: {input_str}") from e

    # Try natural language date parsing with dateutil
    try:
        # Use dateutil parser for flexible date parsing
        # Note: this can be quite permissive, so we put it last
        parsed = dateutil_parser.parse(input_str, default=today)

        # Normalize to midnight (remove time component)
        parsed = datetime(parsed.year, parsed.month, parsed.day)

        return (parsed, True)
    except (ValueError, dateutil_parser.ParserError) as e:
        # If all parsers fail, raise a helpful error
        raise ValueError(
            f"Invalid date or duration format: '{input_str}'. "
            "Supported formats:\n"
            "  - Durations: 1w, 2d, 3m, 1y\n"
            "  - Keywords: today, tomorrow, yesterday, next week, next month, next year\n"
            "  - ISO dates: 2025-10-30\n"
            "  - Natural dates: Oct 30, October 30 2025"
        ) from e


def format_date_input(input_str: str, parsed_value: Union[datetime, timedelta], is_absolute: bool) -> str:
    """Format date or duration input for display.

    Args:
        input_str: Original input string
        parsed_value: Parsed datetime or timedelta
        is_absolute: Whether this is an absolute date

    Returns:
        Human-readable formatted string

    Examples:
        >>> format_date_input("1w", timedelta(days=7), False)
        '+1 week'
        >>> format_date_input("tomorrow", datetime(2025, 10, 24), True)
        'tomorrow (2025-10-24)'
        >>> format_date_input("2025-10-30", datetime(2025, 10, 30), True)
        '2025-10-30'
    """
    if is_absolute:
        # For absolute dates, show the input and the parsed date
        assert isinstance(parsed_value, datetime)
        date_str = parsed_value.strftime("%Y-%m-%d")

        # If input is a keyword, show both keyword and date
        keywords = ["today", "tomorrow", "yesterday", "next week", "next month", "next year"]
        if input_str.lower().strip() in keywords:
            return f"{input_str} ({date_str})"
        else:
            # For ISO dates or natural dates, just show the date
            return date_str
    else:
        # For durations, use the existing format_duration function
        from taskrepo.utils.duration import format_duration

        return format_duration(input_str)
