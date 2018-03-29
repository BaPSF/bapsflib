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
    def __init__(self, command_list):
        super().__init__()

        # set command list
        self._cl = command_list

    def apply_patterns(self, patterns):
        # initialize new cl dict
        cls_dict = {}

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

        # remove trivial command lists
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
                # ensure all command list elements have the same type
                del cls_dict[name]

                # issue warning
                warn(
                    "Symbolic group ({}) removed since ".format(name)
                    + "all entries in 'command list' do NOT have the"
                    + "same type")
            elif isinstance(cls_dict[name]['command list'], str):
                if all(command.stip() == ''
                       for command in cls_dict[name]['command list']):
                    # string command list is nonsensical
                    del cls_dict[name]

                    # issue warning
                    warn(
                        "Symbolic group ({}) removed ".format(name)
                        + "since all entries in 'command list' are "
                        + "null strings")

        # determine if parse was successful
        success = True
        if len(cls_dict) == 0:
            # dictionary is empty
            success = False
        elif len(cls_dict) == 1 and 'remainder' in cls_dict:
            # only 'remainder' is in dictionary
            success = False

        # return
        return success, cls_dict

    def try_patterns(self, patterns):
        # turn string into list
        if isinstance(patterns, str):
            patterns = [patterns]

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
