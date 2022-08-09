from typing import Optional, Union
import ast


def decode_bytes(message: Optional[bytes]) -> Union[None, int, dict]:
    try:
        decoded_message = ast.literal_eval(message.decode())
    except Exception:
        return None
    if type(decoded_message) in (int, dict):
        return decoded_message
    return None


def check_dict(dictionary, keys):
    if dictionary is None:
        return
    if not type(dictionary) is dict:
        return
    if list(dictionary.keys()) != keys:
        return
    return dictionary


def get_integer(text: Optional[str]) -> Optional[int]:
    if not text:
        return None

    string_with_digits = "".join([char for char in text if char.isdigit()])

    if not string_with_digits:
        return None

    return int(string_with_digits)


def get_float(text: Optional[str]) -> Optional[float]:
    if not text:
        return None

    string_with_digits = "".join([char for char in text if char.isdigit() or char == "."])

    if not string_with_digits:
        return None

    if string_with_digits.count(".") > 1:
        return None

    return float(string_with_digits)
