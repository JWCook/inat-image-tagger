"""Type conversion, validation, and formatting utilities"""
from datetime import datetime
from dateutil.parser import parse as parse_date
from typing import Any, Dict, Optional, Tuple

from naturtag.constants import Coordinates


# TODO: This could be moved to pyinaturalist.response_format
def convert_coord_pair(value: str) -> Coordinates:
    if str(value).count(',') != 1:
        return None
    lat, long = str(value).split(',')
    return convert_float(lat), convert_float(long)


def convert_float(value: Any) -> Optional[float]:
    """ Convert a value to a float, if valid; return ``None`` otherwise """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def convert_int_dict(int_dict) -> Dict[int, int]:
    """Convert JSON string keys to ints"""
    return {try_int(k): try_int(v) for k, v in int_dict.items()}


def try_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def format_const(value: str) -> str:
    return str(value).upper().replace('_', '-')


def format_dimensions(dimensions: Dict[str, int]) -> Tuple[int, int]:
    """Slightly simplify 'dimensions' response attribute into ``(width, height)`` tuple"""
    return dimensions.get("width", 0), dimensions.get("height", 0)


def format_file_size(value):
    """Convert a file size in bytes into a human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(value) < 1024.0:
            return f'{value:.2f}{unit}'
        value /= 1024.0
    return f'{value:.2f}TB'


def is_expired(timestamp, expiry_hours):
    """Determine if a timestamp is older than a given expiration length"""
    try:
        last_updated = parse_date(timestamp)
    except (TypeError, ValueError):
        return True

    delta = datetime.now() - last_updated
    elapsed_hours = delta.total_seconds() / 60 / 60
    return int(elapsed_hours) >= expiry_hours
