from .jsonreader import JsonReader
from typing import Any


def json_parse(input: Any) -> Any:
    """
    Parses JSON data from various input sources using a streaming approach.

    This function provides a way to parse JSON content from different input types without
    loading the entire content into memory at once. It uses the :py:class:`.JsonReader` class
    internally to perform the streaming parsing.

    The input is expected to be a binary file-like object,
    but str and bytes can be used as well.

    This function is mostly used for testing.

    Args:
        input: The JSON data to parse

    Returns:
        The parsed JSON value
    """
    with JsonReader(input) as json_reader:
        return json_reader.next_json()
