from enum import Enum, IntEnum
import logging
import re
from typing import Type


class FilterType(Enum):
    STARTSWITH = "startswith"
    ENDSWITH = "endswith"
    CONTAINS = "contains"
    REGEX = "regex"
    EQUAL = "equal"


class FilterValue(Enum):
    INTERNALNAME = "internalName"
    DISPLAYNAME = "displayName"
    ID = "id"


def get_display_name(column: str, idx: int = None) -> str:
    """
    Returns the display name for a column, optionally including an index.

    Args:
        column (str): The name of the column.
        idx (int, optional): The index to include in the display name. Defaults to None.

    Returns:
        str: The display name for the column.
    """
    if idx:
        return f"{column} ({idx:03})"
    else:
        return column


def get_internal_name(column: str, idx: int = None) -> str:
    """
    Returns the sanitized internal name for a column, optionally including an index.

    Args:
        column (str): The name of the column.
        idx (int, optional): The index to include in the internal name. Defaults to None.

    Returns:
        str: The sanitized internal name for the column.
    """
    return get_sanitized_name(get_display_name(column, idx))


def get_import_name(column: str, idx: int = None) -> str:
    """
    Returns the import name for a column, optionally including an index.

    Args:
        column (str): The name of the column.
        idx (int, optional): The index to include in the import name. Defaults to None.

    Returns:
        str: The import name for the column.
    """
    return get_display_name(column, idx)


def get_sanitized_name(displayName: str) -> str:
    """
    Returns a sanitized version of the display name, suitable for use as an internal name.

    Args:
        displayName (str): The display name to sanitize.

    Returns:
        str: The sanitized name.
    """
    sanitized_name = re.sub(r"[^a-z0-9_]", "_", displayName.lower()).strip()
    if sanitized_name.startswith("_"):
        sanitized_name = "underscore_" + sanitized_name[1:]
    if len(sanitized_name) > 1 and sanitized_name[0] in ["1","2","3","4","5","6","7","8","9"]:
        sanitized_name = "int_" + sanitized_name
    return sanitized_name


def log_error(error_message: str, error_type: Type[BaseException] = ValueError) -> None:
    """
    Logs an error message and raises an exception of the specified type.

    Args:
        error_message (str): The error message to log and include in the exception.
        error_type (Type[BaseException]): The type of exception to raise. Defaults to ValueError.

    Raises:
        BaseException: The exception of the specified type with the provided error message.
    """
    logging.error(error_message)
    raise error_type(error_message)
