import ijson  # type: ignore[import-untyped]
import decimal
from typing import Any, TypedDict
from io import BytesIO


class _StackElement(TypedDict):
    value: Any
    name: str | None


class JsonReader:
    """
    A streaming JSON reader that allows streaming parsing of JSON data.
    The current implementation uses `ijson <https://pypi.org/project/ijson/>`__.
    Exceptions are raised as ijson.JsonError.

    JsonReader provides methods to navigate through a JSON structure without loading
    the entire content into memory. This is particularly useful for processing large
    JSON files or streams efficiently.
    """

    _next_event: tuple[str, Any] | None

    def __init__(self, input: Any, **kwargs: Any):
        """
        Creates a new JsonReader that reads from the specified input.
        The input is expected to be a binary file-like object,
        but str and bytes can be used as well.
        """
        if isinstance(input, str):
            input = BytesIO(input.encode("utf-8"))
        self.input = input
        self._next_event = None
        self.eof = False
        self.events = ijson.basic_parse(input, **kwargs)

    def close(self) -> None:
        """Closes the input and releases any resources associated with it."""
        self.eof = True
        if hasattr(self.input, "close"):
            self.input.close()

    def __enter__(self):  # type: ignore[no-untyped-def]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore[no-untyped-def]
        self.close()

    def peek(self) -> str | None:
        """
        Looks at the next token in the JSON stream without consuming it.

        This method allows you to check what type of token is coming next
        without advancing the reader position.

        Returns:
            The type of the next token, or None if the end of the stream has been reached.
        """
        next_event = self._peek_value()
        if next_event is None:
            return None
        return next_event[0]

    def _peek_value(self) -> tuple[str, Any] | None:
        if self.eof:
            return None
        if self._next_event is not None:
            return self._next_event
        try:
            self._next_event = next(self.events)
            return self._next_event
        except StopIteration:
            self.close()
            return None

    def _expect_and_consume(self, event: str) -> Any:
        next_event = self._peek_value()
        if next_event is None or next_event[0] != event:
            raise ijson.JSONError(f"not at {event}, at {'None' if next_event is None else next_event[0]}")
        else:
            res = next_event[1]
            self._next_event = None
            return res

    def start_array(self) -> None:
        """
        Consumes the beginning of a JSON array.

        Raises:
            JSONError: if the next token is not the beginning of an array ('[')
        """
        self._expect_and_consume("start_array")

    def end_array(self) -> None:
        """
        Consumes the end of a JSON array.

        Raises:
            JSONError: if the next token is not the end of an array (']')
        """
        self._expect_and_consume("end_array")

    def start_map(self) -> None:
        """
        Consumes the beginning of a JSON object.

        Raises:
            JSONError: if the next token is not the beginning of an object ('{')
        """
        self._expect_and_consume("start_map")

    def end_map(self) -> None:
        """
        Consumes the end of a JSON object.

        Raises:
            JSONError: if the next token is not the end of an object ('}')
        """
        self._expect_and_consume("end_map")

    def has_next(self) -> bool:
        """
        Checks if there are more elements in the current array or object.

        This method is typically used in a while loop to iterate through
        all elements in an array or all properties in an object.

        Returns:
            True if there are more elements, or False if the end of the
            current array or object has been reached

        Examples::

            reader.start_array()
            while reader.has_next():
                print(reader.next_string())
            reader.end_array()
        """
        next_event = self._peek_value()
        if next_event is None or next_event[0] == "end_map" or next_event[0] == "end_array":
            return False
        return True

    def next_map_key(self) -> str:
        """
        Reads the name of the next property in a JSON object.

        Returns:
            The name of the property

        Raises:
            JSONError: if the next token is not a property name

        Examples::

            reader.start_map()
            while reader.has_next():
                property_name = reader.next_map_key()
                print(property_name)
                reader.skip_value()
            reader.end_map()
        """
        return self._expect_and_consume("map_key")

    def next_json(self) -> Any:
        """
        Reads the next complete JSON value (object, array, or primitive).

        This method parses and returns the entire next value in the JSON stream,
        regardless of its complexity. It's useful when you want to read a complete
        JSON structure without manually navigating through it.

        Returns:
            The parsed JSON value

        Raises:
            JSONError: if the JSON is invalid or incomplete

        Examples::

            # assuming the JSON value is: [{"manager": {"name": "Jane"}}, {"manager": {"name": "Alice"}}]
            result = reader.next_json()
            print(result[1]['manager']['name']) # prints 'Alice'
        """
        next_event = self._peek_value()
        if (
            next_event is None
            or next_event[0] == "end_map"
            or next_event[0] == "end_array"
            or next_event[0] == "map_key"
        ):
            raise ijson.JSONError(f"next_json not available, at {'None' if next_event is None else next_event[0]}")
        stack: list[_StackElement] = []
        while True:
            next_event = self._peek_value()
            assert next_event is not None
            type = next_event[0]
            found_json = False
            json = None
            if type == "start_map":
                stack.append({"value": {}, "name": None})
            elif type == "start_array":
                stack.append({"value": [], "name": None})
            elif type == "end_map":
                found_json = True
                json = stack.pop()["value"]
            elif type == "end_array":
                found_json = True
                json = stack.pop()["value"]
            elif type == "map_key":
                top = stack[-1]
                top["name"] = next_event[1]
            elif type == "number" or type == "integer" or type == "double":
                found_json = True
                json = next_event[1]
                if isinstance(json, decimal.Decimal):
                    json = float(json)
            else:
                found_json = True
                json = next_event[1]
            self._next_event = None
            if found_json:
                if len(stack) == 0:
                    self._peek_value()
                    return json
                top = stack[-1]
                if top["name"] is not None:
                    top["value"][top["name"]] = json
                else:
                    top["value"].append(json)
                top["name"] = None

    def skip_value(self) -> None:
        """
        Skips the next value in the JSON stream.

        Raises:
            JSONError: if there is no more JSON to read, or if the next token is a property name

        Examples::

            reader.start_map()
            while reader.has_next():
                property_name = reader.next_map_key()
                if property_name == "importantProperty":
                    value = reader.next_string()
                    print(value)
                else:
                    print(f'Skipping {property_name}')
                    reader.skip_value()
            reader.end_map()
        """
        next_event = self._peek_value()
        if next_event is None or next_event[0] == "map_key":
            raise ijson.JSONError(f"skip_value not available, at {'None' if next_event is None else next_event[0]}")
        count = 0
        while True:
            if next_event is None:
                break
            if next_event[0] == "start_map" or next_event[0] == "start_array":
                count += 1
            if next_event[0] == "end_map" or next_event[0] == "end_array":
                count -= 1
            self._next_event = None
            if count == 0:
                break
            next_event = self._peek_value()

    def next_json_primitive(self) -> Any:
        """
        Reads the next JSON primitive value.

        Returns:
            The primitive value

        Raises:
            JSONError: if the next token is not a primitive value
        """
        next_event = self._peek_value()
        if next_event is None or next_event[0] not in [
            "null",
            "boolean",
            "integer",
            "double",
            "number",
            "string",
        ]:
            raise ijson.JSONError(
                f"next_json_primitive not available, at {'None' if next_event is None else next_event[0]}"
            )
        res = next_event[1]
        if isinstance(res, decimal.Decimal):
            res = float(res)
        self._next_event = None
        return res

    def next_string(self) -> str:
        """
        Reads the next value as a string.

        If the next value is already a string, it is returned as is.
        If the next value is another primitive type, it is converted
        to a string.

        Returns:
            The string value

        Raises:
            JSONError: if the next token is not a primitive value
        """
        value = self.next_json_primitive()
        if value is None:
            return "null"
        if value == True:
            return "true"
        if value == False:
            return "false"
        if type(value) is str:
            return value
        # TODO for numbers, using Python stringify rather than equivalent of JSON.stringify
        return str(value)

    def next_null(self) -> None:
        """
        Reads the next value as null.

        Returns:
            The null value

        Raises:
            JSONError: if the next token is not null
        """
        next_event = self._peek_value()
        if next_event is None or next_event[0] not in [
            "null",
        ]:
            raise ijson.JSONError(f"next_null not available, at {'None' if next_event is None else next_event[0]}")
        res = next_event[1]
        self._next_event = None
        return res

    def next_boolean(self) -> bool:
        """
        Reads the next value as a boolean.

        Returns:
            The boolean value

        Raises:
            JSONError: if the next token is not a boolean
        """
        next_event = self._peek_value()
        if next_event is None or next_event[0] not in [
            "boolean",
        ]:
            raise ijson.JSONError(f"next_boolean not available, at {'None' if next_event is None else next_event[0]}")
        res = next_event[1]
        self._next_event = None
        return res

    def next_number(self) -> int | float:
        """
        Reads the next value as a number.

        Returns:
            The number value

        Raises:
            JSONError: if the next token is not a number
        """
        next_event = self._peek_value()
        if next_event is None or next_event[0] not in [
            "integer",
            "double",
            "number",
        ]:
            raise ijson.JSONError(f"next_number not available, at {'None' if next_event is None else next_event[0]}")
        res = next_event[1]
        if isinstance(res, decimal.Decimal):
            res = float(res)
        self._next_event = None
        return res
