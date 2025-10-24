from cnri_json_streaming import json_parse
from typing import Any, cast
from io import BytesIO
import json
import pytest
import os


def fail(value: Any) -> None:
    raise Exception("Infinity and NaN not allowed")


def perform_test(path: str) -> None:
    with open(path, "rb") as file:
        json_bytes = file.read()
    try:
        json1 = json.loads(json_bytes, parse_constant=fail)
        json1Exception = None
    except Exception as e:
        json1 = None
        json1Exception = e
    try:
        json2 = json_parse(json_bytes)
        json2Exception = None
    except Exception as e:
        json2 = None
        json2Exception = e
    if json1Exception is None and json2Exception is None:
        assert json.dumps(json1) == json.dumps(json2)
    elif json1Exception is None:
        print(path)
        print(json2Exception)
        assert False, "expected success but failed\n" + json.dumps(json1) + "\n" + str(json2Exception)
    elif json2Exception is None:
        print(path)
        print(json1Exception)
        assert False, "expected failure but succeeded\n" + str(json1Exception) + "\n" + json.dumps(json2)
    else:
        assert True, "both failed"


os.system("rm -rf tmp && mkdir tmp && cd tmp && npm install --no-save @cnri/json-parsing-test-cases")

with open("tmp/node_modules/@cnri/json-parsing-test-cases/json-files.txt", "r") as file:
    paths = file.read().splitlines()


@pytest.fixture(scope="session", autouse=True)
def cleanup(request: Any) -> None:
    def remove_tmp() -> None:
        os.system("rm -rf tmp")

    request.addfinalizer(remove_tmp)


# Most of these are character oddities; exceptions are that we accept form-feed as whitespace, and can't parse a really huge exponent
known_failures_character_oddities = [
    "JSONTestSuite/test_transform/string_1_escaped_invalid_codepoint.json",
    "JSONTestSuite/test_transform/string_2_invalid_codepoints.json",
    "JSONTestSuite/test_transform/string_2_escaped_invalid_codepoints.json",
    "JSONTestSuite/test_transform/string_3_invalid_codepoints.json",
    "JSONTestSuite/test_transform/string_1_invalid_codepoint.json",
    "JSONTestSuite/test_transform/string_3_escaped_invalid_codepoints.json",
    "JSONTestSuite/test_parsing/i_string_incomplete_surrogates_escape_valid.json",
    "JSONTestSuite/test_parsing/i_string_UTF-16LE_with_BOM.json",
    "JSONTestSuite/test_parsing/i_string_invalid_surrogate.json",
    "JSONTestSuite/test_parsing/i_string_1st_valid_surrogate_2nd_invalid.json",
    "JSONTestSuite/test_parsing/i_object_key_lone_2nd_surrogate.json",
    "JSONTestSuite/test_parsing/i_string_utf16BE_no_BOM.json",
    "JSONTestSuite/test_parsing/i_string_UTF8_surrogate_U+D800.json",
    "JSONTestSuite/test_parsing/i_string_1st_surrogate_but_2nd_missing.json",
    "JSONTestSuite/test_parsing/i_string_inverted_surrogates_U+1D11E.json",
    "JSONTestSuite/test_parsing/i_string_utf16LE_no_BOM.json",
    "JSONTestSuite/test_parsing/i_string_invalid_lonely_surrogate.json",
    "JSONTestSuite/test_parsing/i_structure_UTF-8_BOM_empty_object.json",
    "JSONTestSuite/test_parsing/i_string_incomplete_surrogate_pair.json",
    "JSONTestSuite/test_parsing/i_string_incomplete_surrogate_and_escape_valid.json",
    "JSONTestSuite/test_parsing/i_string_lone_second_surrogate.json",
]
known_failures_other = [
    "JSONTestSuite/test_parsing/n_structure_whitespace_formfeed.json",
    "JSONTestSuite/test_parsing/i_number_huge_exp.json",
]


@pytest.mark.parametrize("path", paths)
def test(path: str) -> None:
    if path in known_failures_character_oddities + known_failures_other:
        return
    perform_test("tmp/node_modules/@cnri/json-parsing-test-cases/" + path)
