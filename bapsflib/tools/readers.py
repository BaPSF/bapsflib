__all__ = ["where_size", "compare_binaries"]

import struct
from typing import Any, Dict

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


def where_size(data, size=500):
    """
    Find potential locations in the binary data ``data`` where the array
    size ``size`` is located.  It is assumed the ctype representing
    ``size`` is an unsigned short (2 bytes).

    Returns a tuple of integers representing the starting index of all
    potential locations.
    """
    ndata = len(data)

    previous_offset = 0
    offsets = []
    for offset in range(ndata - 1):
        val = struct.unpack_from("<H", data, offset)[0]

        if val == size:
            offsets.append(offset)
            print(
                f"{offset:6d} ( ∆{offset - previous_offset:6d} ) "
                f"- [ {data[offset - 4:offset].hex(' ', 2)} "
                f"| {val} "
                f"| {data[offset + 2:offset + 10].hex(' ', 2)} ]"
            )
            previous_offset = offset

    return tuple(offsets)


def compare_binaries(b1, b2, verbose=False):
    """
    Take two byte strings ``b1`` and ``b2`` and print their comparison
    to screen.  Differences are highlighted in red.
    """
    offset = 0
    b1_size = len(b1)
    b2_size = len(b2)
    min_size = min(b1_size, b2_size)
    max_size = max(b1_size, b2_size)

    while offset < min_size:
        sub1 = b1[offset:offset + 16]
        sub2 = b2[offset:offset + 16]

        if sub1 != sub2:
            sub1_str = ""
            sub2_str = ""
            highlight = False
            for s1, s2 in zip(sub1.hex(' ', 2), sub2.hex(' ', 2)):
                if s1 != s2 and highlight:
                    sub1_str += s1
                    sub2_str += s2
                elif s1 != s2:
                    highlight = True
                    sub1_str += f"\033[91m{s1}"
                    sub2_str += f"\033[91m{s2}"
                elif s1 == s2 and highlight:
                    highlight = False
                    sub1_str += f"{s1}\033[0m"
                    sub2_str += f"{s2}\033[0m"
                else:
                    sub1_str += s1
                    sub2_str += s2

            if highlight:
                highlight = False
                sub1_str += f"\033[0m"
                sub2_str += f"\033[0m"

            print(f"{offset:6d}  -  {sub1_str}  |  {sub2_str}")
        elif verbose:
            print(f"{offset:6d}  -  {sub1.hex(' ', 2)}  |  {sub2.hex(' ', 2)}")

        offset += 16


def _unpack(data: bytes, offset: int):
    _types = tuple(c_format_chars.keys())
    conversions = {}

    for _type in _types:
        try:
            result = struct.unpack_from(f"<{_type}", data, offset)

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


# def _unpack_array(data: bytes, offset: int = 0) -> dict:
#     sub_data = data[offset:]
#     _bytes = {
#         "header": sub_data[:4],
#         "size": sub_data[4:6],
#         "pad": sub_data[6:10],
#         "array": None,
#         "remainder": None,
#     }
#
#     size = struct.unpack("<h", _bytes["size"])[0]
#     byte_size = 8 * size
#     _bytes["array"] = sub_data[10:10 + byte_size]
#     _bytes["remainder"] = sub_data[10 + byte_size:]
#     return _bytes
#
#
# def _unpack_binary(data: bytes):
#     _bytes = {
#         "header": data[:294],
#     }
#     sub_data = data[294:]
#     index = 0
#     while len(sub_data) > 4010:
#         name = f"arr_{index}"
#         _bytes[name] = _unpack_array(sub_data, offset=0)
#
#         sub_data = _bytes[name]["remainder"]
#         index += 1
#
#     return _bytes


def _unpack_dat_header(data: bytes) -> Dict[str, slice | Tuple[str]]:
    """
    Unpack and examine the header bytes ``[0:294]`` of the binary data
    ``data``.  The deciphered data is collected and returned in a
    dictionary containing keys:

    - ``"dat_arrays"`` : `tuple` of identified traces contained in the
      binary data
    - ``"slice"`` : `slice` object representing the location of the
      header bytes in ``data``.

    """
    # Note:
    #   The .DAT header from the HP E5100A Network Analyzer is always
    #   294 characters long.
    #
    if len(data) < 294:
        raise ValueError("Not enough data")

    if data[:8] != b"\x00\x00\x00\x00\x00\x88\xc3\x40":
        raise ValueError(
            "The binary file is not recognized as a .DAT written by the "
            "HP E5100A Network Analyzer."
        )

    if data[8:16] != b"\x00\x00\x00\x00\x2a\x75\xa5\x41":
        raise ValueError(
            "The binary file is not recognized as a .DAT written by the "
            "HP E5100A Network Analyzer."
        )

    results = {
        "dat_arrays": (),
        "slice": slice(0, 294, 1),
    }

    possible_traces = ("calibration", "raw", "data", "mem", "formd", "main", "sub")

    # determine which traces were turned on
    header = data[results["slice"]]
    trace_binaries = header[-4*7:]
    traces = []
    for index, trace in enumerate(possible_traces):
        start_index = 4 * index
        is_active = struct.unpack("<i", trace_binaries[start_index:start_index + 4])[0]
        if is_active == 1:
            traces.append(trace)

    results["dat_arrays"] = tuple(traces)

    return results


def _unpack_dat_array_calibration(
    data: bytes, offset: int
) -> Dict[str, str | int | Dict[str, slice | int | np.ndarray]]:
    """
    Unpack binary data ``data`` associated with a calibration trace.

    The return dictionary looks like:

    .. code-block:: python

        {
            "array_type": "calibration",  # name of trace
            "size": int, # number of elements in the trace arrays
            "trace_0": {
                "slice": slice,  # slice object for the binary being converted
                "n_arrays": 3, # number of arrays in the trace
                "arr0": numpy.ndarray,  # 1st array
                "arr1": numpy.ndarray,  # 2nd array
                "arr2": numpy.ndarray,  # 3rd array
            },
            "trace_1": {
                "slice": slice,  # slice object for the binary being converted
                "n_arrays": 3, # number of arrays in the trace
                "arr0": numpy.ndarray,  # 1st array
                "arr1": numpy.ndarray,  # 2nd array
                "arr2": numpy.ndarray,  # 3rd array
            },
        }
    """
    results = {
        "array_type": "calibration"
    }  # type: Dict[str, str | int | Dict[str, slice | int | np.ndarray]]

    # - Every saved array has 2 trace entities in the binary file.
    # - The calibration array is actually 3 arrays of calibration
    #   coefficients, where:
    #     1. each calibration coefficient array is separated by a 4 bit buffer
    #     2. the array elements are complex values
    #     3. array elements are written as an 8 bit float for the real component
    #        followed by an 8 bit float for the imaginary component
    # - The binary format for the calibration trace looks like...
    #
    #                            | 1st array                               |
    #  | header |  size | buffer | 1st Re | 1st Im | ... | nth Re | nth Im |
    #  | 4 bit  | 2 bit | 4 bit  | 8 bit  | 8 bit  | ... | 8 bit  | 8 bit  |
    #
    #           | 2nd array                               |
    #  | buffer | 1st Re | 1st Im | ... | nth Re | nth Im |
    #  | 4 bit  | 8 bit  | 8 bit  | ... | 8 bit  | 8 bit  |
    #
    #           | 3rd array                               |
    #  | buffer | 1st Re | 1st Im | ... | nth Re | nth Im |
    #  | 4 bit  | 8 bit  | 8 bit  | ... | 8 bit  | 8 bit  |

    array_size = struct.unpack_from("<H", data, offset+4)[0]
    binary_size = 6 + 3 * (4 + array_size * 16)
    results["size"] = array_size

    # unpack trace_0
    results["trace_0"] = {
        "slice": slice(offset, offset+binary_size, 1),
        "n_arrays": 3,
    }
    offset += 6  # get past header and size bits
    for ii in range(3):
        offset += 4  # get past buffer bits
        arr = np.array(
            struct.unpack_from(f"<{2 * array_size}d", data, offset=offset)
        ).reshape(array_size, 2)
        results["trace_0"][f"arr{ii}"] = arr[..., 0] + 1j * arr[..., 1]

        offset += array_size * 16  # advanced past array bits

    # unpack trace_1
    results["trace_1"] = {
        "slice": slice(offset, offset + binary_size, 1),
        "n_arrays": 3,
    }
    offset += 6  # get past header and size bits
    for ii in range(3):
        offset += 4  # get past buffer bits
        arr = np.array(
            struct.unpack_from(f"<{2 * array_size}d", data, offset=offset)
        ).reshape(array_size, 2)
        results["trace_1"][f"arr{ii}"] = arr[..., 0] + 1j * arr[..., 1]

        offset += array_size * 16  # advanced past array bits

    return results


def _unpack_dat_array(
    data: bytes, array_type: str, offset: int
) -> Dict[str, Any]:
    unpackers = {
        "calibration": _unpack_dat_array_calibration,
    }

    # results = {
    #     "header": data[:4],
    #     "size_binary": data[4:6],
    #     "size": None,
    #     "pad": data[6:10],
    #     "array_binary": None,
    #     "array": None,
    #     "remainder": None,
    # }
    #
    # _size = struct.unpack("<H", results["size_binary"])[0]
    # results["size"] = _size
    # results["array_binary"] = data[10:10 + 8 * _size]
    # results["array"] = np.array(struct.unpack(f"<{_size}d", results["array_binary"]))
    # results["remainder"] = data[10 + 8 * _size:]
    #
    # return results
    return (
        {} if array_type not in unpackers
        else unpackers[array_type](data, offset=offset)
    )


def _unpack_dat(data: bytes, gatekeep: bool = True):
    """
    Unpack and collect the various traces in the binary data (``data``).

    The collected data is returned in a dictionary, where the root keys
    are ``'header'`` or the trace name (e.g. ``'main'``, ``'sub'``,
    etc.).

    Parameters
    ----------
    data : bytes
        The binary data to unpack.

    gatekeep : bool
        Gatekeep the unpacking to binary data that only contains the
        "main" and "sub" traces.  (DEFAULT: `True`)
    """
    # Note:
    #   1. The HP E5100A Network Analyzer saves in the DOS file format,
    #      which utilizes little-endian byte ordering.
    #   2. Each saved "array" has two entries in the binary file that
    #      are identically formatted.
    #      i. trace_0 : I [Erik] do not know what this trace currently
    #                   represents.  I'm suspecting some kine of
    #                   calibration factor.
    #      ii. trace_1 : This is the actual "array" data.
    #
    #   - Using "array" since the binary data can actually be multiple
    #     arrays in a single trace.
    #
    results = {
        "header": _unpack_dat_header(data),
    }

    # Gatekeep
    trace_names = set(results["header"]["dat_arrays"])
    if not isinstance(gatekeep, bool):
        gatekeep = True
    if gatekeep and len(trace_names) != 2:
        raise ValueError(
            f"The binary data contains {len(trace_names)} traces, but functionality "
            f"can only handle binary data with the main and sub traces."
        )
    if gatekeep and len(trace_names - {"main", "sub"}) != 0:
        raise ValueError(
            f"Functionality can only handle binary data with the main and sub"
            f" traces, the binary data contains traces for {trace_names}."
        )

    offset = results["header"]["slice"].stop
    array_types = results["header"]["dat_arrays"]
    for atype in array_types:
        results[atype] = _unpack_dat_array(data, atype, offset=offset)
        offset = results[atype]["trace_1"]["slice"].stop

    return results


def read_na_hp_e5100a_ascii():
    ...

def read_na_hp_e5100a_binary():
    ...

def read_network_analyzer():
    ...
