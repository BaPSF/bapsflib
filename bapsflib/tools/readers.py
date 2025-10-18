import struct

import numpy as np

c_format_chars = {
    "c": {"ctype": "char", "length": 1},
    "b": {"ctype": "signed char", "length": 1},
    "B": {"ctype": "unsigned char", "length": 1},
    "?": {"ctype": "bool", "length": 1},
    "h": {"ctype": "short", "length": 2},
    "H": {"ctype": "unsigned short", "length": 2},
    "e": {"ctype": "half precision", "length": 2},
    "i": {"ctype": "int", "length": 4},
    "I": {"ctype": "unsigned int", "length": 4},
    "l": {"ctype": "long", "length": 4},
    "L": {"ctype": "unsigned long", "length": 4},
    "f": {"ctype": "float", "length": 4},
    "q": {"ctype": "long long", "length": 8},
    "Q": {"ctype": "unsigned long long", "length": 8},
    "d": {"ctype": "double", "length": 8},
    "F": {"ctype": "float complex", "length": 8},
    "D": {"ctype": "double complex", "length": 16},
}

def _unpack(data: bytes, offset: int):
    _types = tuple(c_format_chars.keys())
    conversions = {}

    for _type in _types:
        try:
            result = struct.unpack_from(f"={_type}", data, offset)

            if _type != "c":
                pass
            elif result[0] == b"\x00":
                continue
            else:
                result = [result[0].decode("ascii")]

            conversions[_type] = result[0]
        except (struct.error, TypeError, UnicodeDecodeError):
            continue

    # print(conversions)
    return conversions


def read_na_hp_e5100a_ascii():
    ...

def read_na_hp_e5100a_binary():
    ...

def read_network_analyzer():
    ...
