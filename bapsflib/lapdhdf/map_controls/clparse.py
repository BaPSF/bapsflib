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
import re
from warnings import warn


class CLParse(object):
    """
    Class for parsing RE from a command list. (A command list is a list
    of strings where each string is a set of commands sent to a control
    device to define that control device's state.)
    """
    def __init__(self, command_list):
        """
        :param command_list: the command list for a control device
        :type command_list: list of strings
        """
        super().__init__()

        # set command list
        self._cl = command_list

    def apply_patterns(self, patterns):
        """
        Applies a the REs defined in `patterns` to parse the command
        list.

        :param patterns: list or raw stings defining REs for parsing
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
            >>> patterns = r'(?P<FREQ>(\bFREQ\s)'
            >>>            + r'(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))'
            >>> results = clparse.apply_patterns(patterns)
            >>> results[0]
            True
            >>> results[1]
            {'VOLT': {'cl str': ('VOLT 20.0', 'VOLT 25.0', 'VOLT 30.0'),
                      'command list': (20.0, 25.0, 30.0),
                      're pattern': re.compile(pattern, re.UNICODE)}}
        """
        # initialize new cl dict
        cls_dict = {}

        # condition patterns
        if isinstance(patterns, str):
            # convert string to list
            patterns = [patterns]
        elif isinstance(patterns, (list, tuple)):
            # ensure all entries are strings
            if not all(isinstance(pat, str) for pat in patterns):
                raise ValueError("first argument must be a string of "
                                 "list of strings")

            # ensure all entries are unique
            patterns = list(set(patterns))
        else:
            raise ValueError(
                "first argument must be a string of list of strings")

        # compile all patterns
        for pattern in patterns:
            rpat = re.compile(pattern)

            # confirm each pattern has 2 symbolic group names
            # 1. 'NAME' -- name of the new probe state value
            # 2. 'VAL' -- the value associated with 'NAME'
            #
            if len(rpat.groupindex) == 2:
                # ensure the VAL symbolic group is defined
                if 'VAL' not in rpat.groupindex:
                    raise ValueError(
                        'user needs to define symbolic group VAL for '
                        'the value of the probe state')

                # get name symbolic group name
                sym_groups = list(rpat.groupindex)
                name = sym_groups[0] if sym_groups.index('VAL') == 1 \
                    else sym_groups[1]

                # check symbolic group is not already defined
                if name in cls_dict:
                    raise ValueError(
                        "Symbolic group ({}) defined".format(name)
                        + " in multiple RE patterns")

                # initialize cls dict entry
                cls_dict[name] = {
                    're pattern': rpat,
                    'command list': [],
                    'cl str': []
                }
            else:
                raise ValueError(
                    "user needs to define two symbolic groups, VAL for"
                    " the value group and NAME for the name of the "
                    "probe state value")

        # add a 'remainder' entry to the cls dict
        cls_dict['remainder'] = {
            're pattern': None,
            'command list': list(self._cl).copy(),
        }
        cls_dict['remainder']['cl str'] = \
            cls_dict['remainder']['command list']

        # scan through probe states (ie re patterns)
        for name in cls_dict:
            # skip the 'remainder' entry
            if name == 'remainder':
                continue

            # search for pattern
            r_cl = []
            for command in cls_dict['remainder']['command list']:
                results = cls_dict[name]['re pattern'].search(command)
                if results is not None:
                    # try to convert the 'VAL' string into float
                    # - for now, assuming 'VAL' will always be a float
                    #   or string, NEVER an integer
                    try:
                        value = float(results.group('VAL'))
                    except ValueError:
                        value = results.group('VAL')

                    # add to command list
                    cls_dict[name]['command list'].append(value)
                    cls_dict[name]['cl str'].append(
                        results.group(name))

                    # make a new remainder command list
                    stripped_cl = command.replace(
                        results.group(name), '').strip()
                    r_cl.append(stripped_cl)
                else:
                    cls_dict[name]['command list'].append(None)
                    cls_dict[name]['cl str'].append(None)

            # update remainder command list
            # - only if the above command list build was not trivial
            #   and all elements of 'command list' have the same type
            #
            if None not in cls_dict[name]['command list'] \
                    and all(isinstance(
                    val, type(cls_dict[name]['command list'][0]))
                    for val in cls_dict[name]['command list']):
                cls_dict['remainder']['command list'] = r_cl
                cls_dict['remainder']['cl str'] = \
                    cls_dict['remainder']['command list']

        # remove trivial command lists and convert lists to tuples
        names = list(cls_dict)
        for name in names:
            if name == 'remainder':
                # remove remainder if it's empty
                if all(val.strip() == ''
                       for val in
                       cls_dict['remainder']['command list']):
                    del cls_dict['remainder']
            elif None in cls_dict[name]['command list']:
                # command list is trivial
                del cls_dict[name]

                # issue warning
                warn(
                    "Symbolic group ({}) removed since ".format(name)
                    + "some or all of the 'command list' has None "
                    + "values")
            elif not all(isinstance(
                    val, type(cls_dict[name]['command list'][0]))
                    for val in cls_dict[name]['command list']):
                # ensure all command list elements have the same
                # type
                del cls_dict[name]

                # issue warning
                warn(
                    "Symbolic group ({}) removed ".format(name)
                    + "since all entries in 'command list' do NOT "
                    + "have the same type")
            elif isinstance(cls_dict[name]['command list'][0], str):
                if all(command.strip() == ''
                       for command
                       in cls_dict[name]['command list']):
                    # string command list is nonsensical
                    del cls_dict[name]

                    # issue warning
                    warn(
                        "Symbolic group ({}) removed ".format(name)
                        + "since all entries in 'command list' are "
                        + "null strings")

            # convert lists to tuples
            # - first check dict `name` has not been deleted
            if name in cls_dict:
                cls_dict[name]['command list'] = \
                    tuple(cls_dict[name]['command list'])
                cls_dict[name]['cl str'] = \
                    tuple(cls_dict[name]['cl str'])

        # determine if parse was successful
        success = True
        if len(cls_dict) == 0:
            # dictionary is empty
            success = False
            cls_dict = None
        elif len(cls_dict) == 1 and 'remainder' in cls_dict:
            # only 'remainder' is in dictionary
            success = False
            cls_dict = None

        # return
        return success, cls_dict

    def try_patterns(self, patterns):
        """
        Prints to the results of applying the REs in patterns to the
        command list.  Pretty print of :meth:`apply_patterns`.

        :param patterns: list or raw stings defining REs for parsing
            the command list
        :type patterns: str or list of strings
        """
        # TODO: clean method and format print better
        #
        # build dictionary
        success, cls_dict = self.apply_patterns(patterns)

        # print results
        hline1 = 'command'.ljust(9) + 'command'.ljust(40)
        hline2 = 'index'.ljust(9) + 'str'.ljust(40)
        for name in cls_dict:
            hline1 += str(name).ljust(10)
            hline2 += type(
                cls_dict[name]['command list'][0]).__name__.ljust(10)
        print(hline1)
        print(hline2)

        for ci, command in enumerate(self._cl):
            line = str(ci).ljust(9) + str(command).ljust(40)

            for name in cls_dict:
                line += str(cls_dict[name]['command list'][ci])

            print(line)
