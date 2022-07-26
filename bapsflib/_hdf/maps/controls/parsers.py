# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2018 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
"""
Module for defining functionality that parses command lists.  Command lists
are a list of strings used by control devices to indicate what is changed from
shot-to-shot.  This usually represents a command string that is sent to a
device to tell it to change an output.
"""
__all__ = ["CLParse"]

import numpy as np
import re

from typing import Iterable, Union
from warnings import warn


class CLParse(object):
    """
    Class for parsing RE from a command list. (A command list is a list
    of strings where each string is a set of commands sent to a control
    device to define that control device's state.)
    """

    def __init__(self, command_list: Union[str, Iterable[str]]):
        """
        :param command_list: the command list for a control device
        :type command_list: list of strings
        """
        super().__init__()

        # condition `command list`
        try:
            if isinstance(command_list, str):
                command_list = [command_list]
            elif isinstance(command_list, Iterable):
                if not all(isinstance(val, str) for val in command_list):
                    raise ValueError
            else:
                raise ValueError
        except ValueError:
            raise ValueError("`command_list` must be a str or an Iterable of strings")

        # set command list
        self._cl = command_list

    def apply_patterns(self, patterns: Union[str, Iterable[str]]):
        """
        Applies a the REs defined in `patterns` to parse the command
        list.

        :param patterns: list or raw strings defining REs for parsing
            the command list
        :type patterns: str or list of strings
        :return: (bool, dict)

        :Example:

            >>> # define a command list
            >>> cl = ['VOLT 20.0', 'VOLT 25.0', 'VOLT 30.0']
            >>>
            >>> # define clparse object
            >>> clparse = CLParse(cl)
            >>>
            >>> # apply patterns
            >>> patterns = (r'(?P<FREQ>(\bFREQ\s)'
            >>>             + r'(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))')
            >>> results = clparse.apply_patterns(patterns)
            >>> results[0]
            True
            >>> results[1]
            {'VOLT': {'cl str': ('VOLT 20.0', 'VOLT 25.0', 'VOLT 30.0'),
                      'command list': (20.0, 25.0, 30.0),
                      're pattern': re.compile(pattern, re.UNICODE),
                      'dtype': numpy.float64}}
        """
        # initialize new cl dict
        cls_dict = {}  # type: dict

        # condition patterns
        if isinstance(patterns, str):
            # convert string to list
            patterns = [patterns]
        elif isinstance(patterns, Iterable):
            # ensure all entries are strings
            if not all(isinstance(pat, str) for pat in patterns):
                raise ValueError("`patterns` must be a str or Iterable of strings")

            # ensure all entries are unique
            patterns = list(set(patterns))
        else:
            raise ValueError("`patterns` must be a string or list of strings")

        # compile all patterns
        for pattern in patterns:
            rpat = re.compile(pattern)

            # confirm each pattern has 2 symbolic group names
            # 1. 'NAME' -- name of the new probe state value
            # 2. 'VAL' -- the value associated with 'NAME'
            #
            if len(rpat.groupindex) == 2:
                # ensure the VAL symbolic group is defined
                if "VAL" not in rpat.groupindex:
                    raise ValueError(
                        "user needs to define symbolic group VAL for "
                        "the value of the probe state"
                    )

                # get name symbolic group name
                sym_groups = list(rpat.groupindex)
                name = sym_groups[0] if sym_groups.index("VAL") == 1 else sym_groups[1]

                # check symbolic group is not already defined
                if name in cls_dict:
                    raise ValueError(
                        f"Symbolic group ({name}) defined in multiple RE patterns"
                    )
                elif name.lower() == "remainder":
                    raise ValueError(f"Can NOT use {name} as a symbolic group name")

                # initialize cls dict entry
                cls_dict[name] = {"re pattern": rpat, "command list": [], "cl str": []}
            else:
                raise ValueError(
                    "user needs to define two symbolic groups, VAL for"
                    " the value group and NAME for the name of the "
                    "probe state value"
                )

        # add a 'remainder' entry to the cls dict
        cls_dict["remainder"] = {
            "re pattern": None,
            "command list": list(self._cl).copy(),
        }
        cls_dict["remainder"]["cl str"] = cls_dict["remainder"]["command list"]

        # scan through state values (ie re patterns)
        # - iterate 'remainder' first
        #
        names = list(cls_dict.keys())
        names.remove("remainder")
        names = ["remainder"] + names
        for name in names:
            # check 'remainder' entry for NULL strings
            # - then skip or break
            if name == "remainder":
                if "" in cls_dict["remainder"]["command list"]:
                    del cls_dict["remainder"]
                    break
                else:  # pragma: no cover
                    # this is not covered due to CPython's peephole
                    # optimizer (see coverage.py issue 198)
                    continue

            # search for pattern
            r_cl = []
            for command in cls_dict["remainder"]["command list"]:
                results = cls_dict[name]["re pattern"].search(command)
                if results is not None:
                    # try to convert the 'VAL' string into float
                    # - for now, assuming 'VAL' will always be a float
                    #   or string, NEVER an integer
                    try:
                        value = float(results.group("VAL"))
                    except ValueError:
                        value = results.group("VAL")  # type: str
                        value = value.strip()
                        if value == "":
                            value = None

                    # add to command list
                    cls_dict[name]["command list"].append(value)
                    cls_dict[name]["cl str"].append(results.group(name))

                    # make a new remainder command list
                    stripped_cmd = command.replace(results.group(name), "").strip()
                    if stripped_cmd == "":
                        stripped_cmd = None
                    r_cl.append(stripped_cmd)
                else:
                    cls_dict[name]["command list"].append(None)
                    cls_dict[name]["cl str"].append(None)

            # update remainder command list
            # - only if the above 'command list' build does NOT produce
            #   trivial (None) elements and all elements of 'command
            #   list' have the same type
            #
            if None not in cls_dict[name]["command list"] and all(
                isinstance(val, type(cls_dict[name]["command list"][0]))
                for val in cls_dict[name]["command list"]
            ):
                cls_dict["remainder"]["command list"] = r_cl
                cls_dict["remainder"]["cl str"] = cls_dict["remainder"]["command list"]

                # delete and break if 'remainder' as trivial elements
                # - i.e. RE can NOT be matched anymore
                #
                if None in cls_dict["remainder"]["command list"]:
                    del cls_dict["remainder"]
                    break

        # remove trivial command lists and convert lists to tuples
        names = list(cls_dict.keys())
        for name in names:
            if None in cls_dict[name]["command list"] or not bool(
                cls_dict[name]["command list"]
            ):
                # command list is trivial
                del cls_dict[name]

                # issue warning
                warn(
                    f"Symbolic group ({name}) removed since some or all of the "
                    f"'command list' has None values"
                )
            elif not all(
                isinstance(val, type(cls_dict[name]["command list"][0]))
                for val in cls_dict[name]["command list"]
            ):
                # ensure all command list elements have the same
                # type
                del cls_dict[name]

                # issue warning
                warn(
                    f"Symbolic group ({name}) removed since all entries in "
                    f"'command list' do NOT have the same type"
                )
            else:
                # condition 'command list' value and determine 'dtype'
                if isinstance(cls_dict[name]["command list"][0], float):
                    # 'command list' is a float
                    cls_dict[name]["dtype"] = np.float64
                else:
                    # 'command list' is a string
                    mlen = len(max(cls_dict[name]["command list"], key=lambda x: len(x)))
                    cls_dict[name]["dtype"] = np.dtype((np.unicode_, mlen))

            # convert lists to tuples
            # - first check dict `name` has not been deleted
            if name in cls_dict:
                cls_dict[name]["command list"] = tuple(cls_dict[name]["command list"])
                cls_dict[name]["cl str"] = tuple(cls_dict[name]["cl str"])

        # determine if parse was successful
        success = True
        if len(cls_dict) == 0:
            # dictionary is empty
            success = False
            cls_dict = {}
        elif len(cls_dict) == 1 and "remainder" in cls_dict:
            # only 'remainder' is in dictionary
            success = False
            cls_dict = {}

        # return
        return success, cls_dict

    def try_patterns(self, patterns: Union[str, Iterable[str]]):
        """
        Prints to the results of applying the REs in patterns to the
        command list.  Pretty print of :meth:`apply_patterns`.

        :param patterns: list or raw strings defining REs for parsing
            the command list
        :type patterns: str or list of strings
        """
        # TODO: clean method and format print better
        #
        # build dictionary
        success, cls_dict = self.apply_patterns(patterns)

        # print results
        hline1 = "command".ljust(9) + "command".ljust(40)
        hline2 = "index".ljust(9) + "str".ljust(40)
        for name in cls_dict:
            hline1 += str(name).ljust(10)
            hline2 += type(cls_dict[name]["command list"][0]).__name__.ljust(10)
        print(hline1)
        print(hline2)

        for ci, command in enumerate(self._cl):
            line = str(ci).ljust(9) + str(command).ljust(40)

            for name in cls_dict:
                line += str(cls_dict[name]["command list"][ci])

            print(line)
