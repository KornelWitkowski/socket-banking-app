from utils import get_float, get_integer, decode_bytes, check_dict

import pytest


@pytest.mark.parametrize(
    "dictionary, expected_output",
    [
        [None, None],
        [232, None],
        [["key1", "key2"], None],
        ['{"key1": 1, "key2": 2}', None],
        [{"key1": 1, "key2": 2}, {"key1": 1, "key2": 2}],
        [{"key1": 1, "key3": 2}, None]
    ],
)
def test_check_dict(dictionary, expected_output):
    output = check_dict(dictionary, ["key1", "key2"])
    assert output == expected_output


@pytest.mark.parametrize(
    "message, expected_output",
    [
        [b'{"a" : 1, "b" : 2}', {"a": 1, "b": 2}],
        [b'54321', 54321],
        ["12.121", None],
        [None, None],
        ["", None],
        ["@@##%$$^%&^", None],
        [b"{'Login': 'login', 'Password': 'login'}", {'Login': 'login', 'Password': 'login'}]
    ],
)
def test_decode_bytes(message, expected_output):
    output = decode_bytes(message)
    assert output == expected_output

@pytest.mark.parametrize(
    "text, expected_output",
    [
        ["d232sddadas", 232],
        ["11sdds322", 11322],
        ["12121", 12121],
        [None, None],
        ["", None],
        ["@@##%$$^%&^", None],
    ],
)
def test_get_integer(text, expected_output):
    output = get_integer(text)
    assert expected_output == output


@pytest.mark.parametrize(
    "text, expected_output",
    [
        ["d232sddadas", 232],
        ["11sdds322", 11322],
        ["12121", 12121],
        [None, None],
        ["", None],
        ["@@##%$$^%&^", None],
        ["1.23", 1.23],
        ["1..23", None],
        [".123", 0.123],
        ["942.", 942.0]
    ],
)
def test_get_float(text, expected_output):
    output = get_float(text)
    assert output == expected_output
