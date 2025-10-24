from cnri_json_streaming import JsonReader
from typing import Any, Set
from io import BytesIO

example = """
{
    "key": "value",
    "number": 17.5,
    "integer": 17,
    "array_of_strings": [
        "string1",
        "string2"
    ],
    "sub_object": {
        "something": "else",
        "array_of_objects": [
            {
                "key": "value1"
            },
            {
                "key": "value2"
            }
        ]
    }
}
"""


def perform_test(input: Any, depth: int) -> None:
    with JsonReader(input) as json_reader:
        json_reader.start_map()
        keys: Set[str] = set()
        while json_reader.has_next():
            key = json_reader.next_map_key()
            keys.add(key)
            if key == "key":
                assert json_reader.next_json() == "value"
            elif key == "number":
                value = json_reader.next_json()
                assert value == 17.5
            elif key == "integer":
                value = json_reader.next_json()
                assert value == 17
            elif key == "array_of_strings":
                if depth == 1:
                    arr = json_reader.next_json()
                    assert arr[0] == "string1"
                    assert arr[1] == "string2"
                else:
                    json_reader.start_array()
                    count = 0
                    while json_reader.has_next():
                        count += 1
                        assert json_reader.next_json() == f"string{count}"
                    json_reader.end_array()
            elif key == "sub_object":
                if depth == 1:
                    obj = json_reader.next_json()
                    assert obj["something"] == "else"
                    assert obj["array_of_objects"][0]["key"] == "value1"
                    assert obj["array_of_objects"][1]["key"] == "value2"
                else:
                    json_reader.start_map()
                    assert json_reader.next_map_key() == "something"
                    assert json_reader.next_json() == "else"
                    assert json_reader.next_map_key() == "array_of_objects"
                    if depth == 2:
                        arr = json_reader.next_json()
                        assert arr[0]["key"] == "value1"
                        assert arr[1]["key"] == "value2"
                    else:
                        count = 0
                        json_reader.start_array()
                        while json_reader.has_next():
                            json_reader.start_map()
                            assert json_reader.next_map_key() == "key"
                            count += 1
                            assert json_reader.next_json() == f"value{count}"
                            json_reader.end_map()
                        json_reader.end_array()
                    json_reader.end_map()
        json_reader.end_map()
        assert json_reader.peek() is None
        assert "key" in keys
        assert "number" in keys
        assert "integer" in keys
        assert "array_of_strings" in keys
        assert "sub_object" in keys


def test_1_string() -> None:
    perform_test(example, 1)


def test_2_string() -> None:
    perform_test(example, 2)


def test_3_string() -> None:
    perform_test(example, 3)


def test_1_buf() -> None:
    input = BytesIO(example.encode("utf-8"))
    perform_test(input, 1)
    assert input.closed


def test_2_buf() -> None:
    input = BytesIO(example.encode("utf-8"))
    perform_test(input, 2)
    assert input.closed


def test_3_buf() -> None:
    input = BytesIO(example.encode("utf-8"))
    perform_test(input, 3)
    assert input.closed


def test_skip_value() -> None:
    with JsonReader(example) as json_reader:
        json_reader.start_map()
        keys: Set[str] = set()
        while json_reader.has_next():
            key = json_reader.next_map_key()
            keys.add(key)
            json_reader.skip_value()
        json_reader.end_map()
        assert json_reader.peek() is None
        assert "key" in keys
        assert "number" in keys
        assert "integer" in keys
        assert "array_of_strings" in keys
        assert "sub_object" in keys
