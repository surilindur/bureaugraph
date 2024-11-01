from datetime import UTC
from datetime import datetime

from rdflib.term import Literal
from rdflib.namespace import XSD


def xsd_datetime(value: datetime) -> Literal:
    """Convert a Python datetime object into literal with datatype xsd:dateTime"""
    return Literal(
        lexical_or_value=value.isoformat(timespec="seconds"),
        datatype=XSD.dateTime,
    )


def xsd_integer(value: int) -> Literal:
    """Convert a Python integer value into literal with datatype xsd:integer"""
    return Literal(
        lexical_or_value=str(value),
        datatype=XSD.integer,
    )


def xsd_boolean(value: bool) -> Literal:
    """Convert a Python boolean value into string literal with datatype xsd:boolean"""
    return Literal(
        lexical_or_value=str(value).lower(),
        datatype=XSD.boolean,
    )


def python_datetime_snowflake(id: int) -> datetime:
    """
    Utility function to convert a Snowflake ID into a timezone-aware datetime.
    """
    return datetime.fromtimestamp(timestamp=((id >> 22) + 1288834974657) / 1000, tz=UTC)


def iso_datetime(value: datetime) -> str:
    """
    Utility function to convert python datetime objects into string.
    The strings will follow the ISO format, without milliseconds or microseconds.
    """
    assert value.tzinfo, f"Timezone-unaware datetime object: {value}"
    return value.isoformat(timespec="seconds")


def hex_rgb(red: int, green: int, blue: int) -> Literal:
    """Utility function to convert an RGB value into a hexadecimal string."""
    return Literal(f"#{red:02x}{green:02x}{blue:02x}")
