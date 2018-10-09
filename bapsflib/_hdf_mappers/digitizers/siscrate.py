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
import astropy.units as u
import h5py
import numpy as np
import os
import re

from bapsflib.utils.errors import HDFMappingError
from typing import (Any, Dict, Tuple, Union)
from warnings import warn

from .templates import HDFMapDigiTemplate


class HDFMapDigiSISCrate(HDFMapDigiTemplate):
    """
    Mapping class for the 'SIS crate' digitizer.

    Simple group structure looks like:

    .. code-block:: none

        +-- SIS crate
        |   +-- config01
        |   |   +-- SIS crate 3302 calibration[0]
        |   |   |   +--
        .
        |   |   +-- SIS crate 3302 configurations[0]
        |   |   |   +--
        .
        |   |   +-- SIS crate 3305 calibration[0]
        |   |   |   +--
        .
        |   |   +-- SIS crate 3305 configurations[0]
        |   |   |   +--
        .
        .
        |   |   +-- SIS crate 3820 configurations[0]
        |   |   |   +--
        |   +-- config01 [Slot 5: SIS 3302 ch 1]
        |   +-- config01 [Slot 5: SIS 3302 ch 1] headers
        .
        .
        .
        |   +-- config01 [Slot 13: SIS 3305 FPGA 1 ch 1]
        |   +-- config01 [Slot 13: SIS 3305 FPGA 1 ch 1] headers
        .
        |   +-- config01 [Slot 13: SIS 3305 FPGA 2 ch 1]
        |   +-- config01 [Slot 13: SIS 3305 FPGA 2 ch 1] headers
        .
        .
        .
    """
    def __init__(self, group: h5py.Group):
        """
        :param group: the HDF5 digitizer group
        """
        # initialize
        HDFMapDigiTemplate.__init__(self, group)

        # define device adc's
        self._device_adcs = ('SIS 3302',
                             'SIS 3305',)  # type: Tuple[str, ...]

        # populate self.configs
        self._build_configs()

    def _adc_info_first_pass(
            self,
            config_name: str,
            adc_name: str
    ) -> Tuple[Tuple[int, Tuple[int, ...], Dict[str, Any]], ...]:
        """
        Gathers the analog-digital-converter's connected board and
        channel numbers, as well as, the associated setup configuration
        for each connected board.

        :param config_name: digitizer configuration name
        :param adc_name: name of analog-digital-converter

        :returns:

            Tuple of 3-element tuples where the 1st element of the
            nested tuple represents a connected *board* number, the 2nd
            element is a tuple of connected *channel* numbers for the
            *board*, and the 3rd element is a dictionary of adc setup
            values (*bit*, *clock rate*, etc.).

        On the first pass, the meta-info dict will contain:

        .. csv-table::
            :header: "Key", "Description"
            :widths: 20, 60

            "::

                'bit'
            ", "
            bit resolution of the digitizer's analog-digital-converter
            "
            "::

                'clock rate'
            ", "
            clock rate of the digitizer's analog-digital-converter
            "
            "::

                'shot average (software)'
            ", "
            number of shots intended to be averaged over
            "
            "::

                'sample average (hardware)'
            ", "
            number of data samples average together
            "
        """
        # digitizer 'Raw data + config/SIS crate' has two adc's,
        # SIS 3302 and SIS 3305
        # adc_info = (
        #     int, # board number
        #     (int, ), # connected channel numbers
        #     {'bit': int, # bit resolution
        #      'clock rate': <Quantity 100.0 MHz>,
        #      'nshotnum: int, # num. of recorded shot numbers
        #      'nt': int, # num. of recorded time samples
        #      'shot average (software)': int,
        #      'sample average (hardware)': int},
        # )
        #
        # initialize
        adc_info = []

        # initialize connections
        # Note:
        #   * conns is a tuple of tuples where each tuple is a seed for
        #     the elements of `adc_info`
        #   * the 'clock rate' for 'SIS 3305' depends on the mode of
        #     the adc which is store in the configuration group.  Thus,
        #     assignment is left to `_find_adc_connections.
        #
        conns = self._find_adc_connections(adc_name, config_name)

        # add 'bit' values to adc_info
        for conn in conns:
            if adc_name == 'SIS 3302':
                conn[2]['bit'] = 16
            elif adc_name == 'SIS 3305':
                conn[2]['bit'] = 10

            # append info
            adc_info.append(conn)

        return tuple(adc_info)

    def _build_configs(self):
        """Builds the :attr:`configs` dictionary."""
        # collect names of datasets and sub-groups
        subgroup_names = []
        dataset_names = []
        for key in self.group.keys():
            if isinstance(self.group[key], h5py.Dataset):
                dataset_names.append(key)
            if isinstance(self.group[key], h5py.Group):
                subgroup_names.append(key)

        # build self.configs
        for name in subgroup_names:
            # determine configuration name
            config_name = self._parse_config_name(name)

            # populate
            if bool(config_name):
                # initialize configuration name in the config dict
                # - add 'config group path'
                self._configs[config_name] = {
                    'config group path': self.group[name].name,
                }

                # determine if config is active
                self._configs[config_name]['active'] = \
                    self.deduce_config_active_status(config_name)

                # assign active adc's to the configuration
                self._configs[config_name]['adc'] = \
                    self._find_active_adcs(self.group[name])

                # define 'shotnum' entry
                self._configs[config_name]['shotnum'] = {
                    'dset field': ('Shot number',),
                    'shape': (),
                    'dtype': np.uint32,
                }

                # initialize adc info
                for adc in self._configs[config_name]['adc']:
                    self._configs[config_name][adc] = \
                        self._adc_info_first_pass(config_name, adc)

                # update adc info with 'nshotnum' and 'nt'
                # - `construct_dataset_name` needs adc info to be seeded
                # - the following updates depend on
                #   construct_dataset_name
                #
                for adc in self._configs[config_name]['adc']:
                    for conn in self._configs[config_name][adc]:
                        if self._configs[config_name]['active']:
                            nshotnum, nt = self._get_dset_shape(
                                config_name, adc, conn)
                            conn[2].update({
                                'nshotnum': nshotnum,
                                'nt': nt
                            })
                        else:
                            conn[2].update({
                                'nshotnum': None,
                                'nt': None
                            })

        # -- raise HDFMappingErrors                                 ----
        #no configurations found
        if not bool(self._configs):
            why = "there are no mappable configurations"
            raise HDFMappingError(self.info['group path'], why=why)

        # ensure there are active configs
        if len(self.active_configs) == 0:
            raise HDFMappingError(
                self.info['group path'],
                "there are not active configurations")

        # if 'adc' is NULL and 'acitve' is True raise HDFMappingError
        # if 'adc' is NULL and 'acitve' is False issue warning
        # ensure active configs are not NULL

    @staticmethod
    def _find_active_adcs(config_group: h5py.Group) -> Tuple[str, ...]:
        """
        Determines active adc's used in the digitizer configuration.

        :param config_group: HDF5 group object of the configuration
            group

        :returns: tuple of active (used) analog-digital-converter names
        """
        active_adcs = []
        adc_types = config_group.attrs['SIS crate board types']
        if 2 in adc_types:
            active_adcs.append('SIS 3302')
        if 3 in adc_types:
            active_adcs.append('SIS 3305')

        return tuple(active_adcs)

    def _find_adc_connections(
            self,
            adc_name: str,
            config_name: str
    ) -> Tuple[Tuple[int, Tuple[int, ...], Dict[str, Any]], ...]:
        """
        Determines active connections on the adc.

        :param adc_name: name of the analog-digital-converter
        :param config_name: digitizer configuration name

        :return:

            Tuple of 3-element tuples where the 1st element of the
            nested tuple represents a connected *board* number, the 2nd
            element is a tuple of connected *channel* numbers for the
            *board*, and the 3rd element is a dictionary of adc setup
            values (*bit*, *clock rate*, etc.).

        On determination of adc connections, the meta-info dict will
        also be populated with:

        .. csv-table::
            :header: "Key", "Description"
            :widths: 20, 60

            "::

                'clock rate'
            ", "
            clock rate of the digitizer's analog-digital-converter
            "
            "::

                'shot average (software)'
            ", "
            number of shots intended to be averaged over
            "
            "::

                'sample average (hardware)'
            ", "
            number of data samples average together
            "
        """
        config_path = self.configs[config_name]['config group path']
        config_group = self.group.get(config_path)
        active = self.configs[config_name]['active']

        # initialize conn
        # conn = list of connections
        #
        conn = []

        # define _helpers
        if adc_name not in ('SIS 3302', 'SIS 3305'):
            warn("Invalid adc name '{}'".format(adc_name))
            return ()
        _helpers = {
            'SIS 3302': {
                'short': '3302',
                're': r"SIS crate 3302 configurations\[(?P<INDEX>\d+)\]",
            },
            'SIS 3305': {
                'short': '3305',
                're': r"SIS crate 3305 configurations\[(?P<INDEX>\d+)\]",
            },
        }

        # Build tuple (slot, config index, board, adc)
        # - build a tuple that pairs the adc name (adc), adc slot
        #   number (slot), configuration group index (index), and
        #   board number (brd)
        #
        slots = config_group.attrs['SIS crate slot numbers']
        indices = config_group.attrs['SIS crate config indices']
        adc_pairs = []
        for slot, index in zip(slots, indices):
            if slot != 3:
                brd, adc = self.slot_to_brd(slot)
                adc_pairs.append((slot, index, brd, adc))

        # Ensure the same configuration index is not assign to multiple
        # slots for the same adc
        for slot, index, brd, adc in adc_pairs:
            for ss, ii, bb, aa in adc_pairs:
                if ii == index and aa == adc and ss != slot:
                    why = ("The same configuration index is assigned "
                           "to multiple slots of the same adc.")
                    if active:
                        raise HDFMappingError(
                            self.info['group path'], why=why)
                    else:
                        why += "...config not active so not adding to " \
                               "mapping"
                        warn(why)
                        return ()

        # gather adc configuration groups
        gnames = []
        for name in config_group:
            _match = re.fullmatch(_helpers[adc_name]['re'], name)
            if bool(_match):
                gnames.append((name, int(_match.group('INDEX'))))

        # Determine connected (brd, ch) combinations
        for name, config_index in gnames:
            # find board number
            brd = None
            for slot, index, board, adc in adc_pairs:
                if adc_name == adc and config_index == index:
                    brd = board
                    break

            # ensure board number was found
            if brd is None:
                why = ("Board not found since group name "
                       + "determined `config_index` "
                       + "{} not".format(config_index)
                       + " defined in top-level configuration group")
                warn(why)
                continue

            # find connected channels
            chs = []
            for key, val in config_group[name].attrs.items():
                if 'Enabled' in key and val == b'TRUE':
                    _patterns = (r"Enabled\s(?P<CH>\d+)",
                                 r"FPGA 1 Enabled\s(?P<CH>\d+)",
                                 r"FPGA 2 Enabled\s(?P<CH>\d+)",)
                    ch = None
                    for pat in _patterns:
                        _match = re.fullmatch(pat, key)
                        if bool(_match):
                            ch = int(_match.group('CH'))
                            if 'FPGA 2' in pat:
                                ch += 4
                            break
                    if ch is not None:
                        chs.append(ch)

            # ensure connected channels are unique
            if len(chs) != len(set(chs)):
                why = ("HDF5 structure unexpected..."
                       + "'{}'".format(config_name + '/' + name)
                       + " does not define a unique set of channel "
                       + "numbers...not adding to `configs` dict")
                warn(why)

                # skip adding to conn list
                continue

            # ensure chs is not NULL
            if len(chs) == 0:
                why = ("HDF5 structure unexpected..."
                       + "'{}'".format(config_name + '/' + name)
                       + " does not define any valid channel "
                       + "numbers...not adding to `configs` dict")
                warn(why)

                # skip adding to conn list
                continue

            # determine shot averaging
            shot_ave = None
            if 'Shot averaging (software)' \
                    in config_group[name].attrs:
                shot_ave = config_group[name].attrs[
                    'Shot averaging (software)']
                if shot_ave == 0 or shot_ave == 1:
                    shot_ave = None

            # determine sample averaging
            sample_ave = None
            if adc_name == 'SIS 3305':
                # the 'SIS 3305' adc does NOT support sample averaging
                pass
            else:
                # SIS 3302
                # - the HDF5 attribute is the power to 2
                # - So, a hardware sample of 5 actually means the number
                #   of points sampled is 2^5
                if 'Sample averaging (hardware)' \
                        in config_group[name].attrs:
                    sample_ave = config_group[name].attrs[
                        'Sample averaging (hardware)']
                    if sample_ave == 0:
                        sample_ave = None
                    else:
                        sample_ave = 2 ** sample_ave

            # determine clock rate
            if adc_name == 'SIS 3305':
                # has different clock rate modes
                try:
                    cr_mode = config_group[name].attrs['Channel mode']
                    cr_mode = int(cr_mode)
                except (KeyError, ValueError):
                    why = ("HDF5 structure unexpected..."
                           + "'{}'".format(config_name + '/' + name)
                           + " does not define a clock rate mode"
                           + "...setting to None in the `configs` dict")
                    warn(why)
                    cr_mode = -1
                if cr_mode == 0:
                    cr = u.Quantity(1.25, unit='GHz')
                elif cr_mode == 1:
                    cr = u.Quantity(2.5, unit='GHz')
                elif cr_mode == 2:
                    cr = u.Quantity(5.0, unit='GHz')
                else:
                    cr = None
            else:
                # 'SIS 3302' has one clock rate mode
                cr = u.Quantity(100.0, unit='MHz')

            # build subconn tuple with connected board, channels, and
            # acquisition parameters
            subconn = (brd, tuple(chs),
                       {'clock rate': cr,
                        'shot average (software)': shot_ave,
                        'sample average (hardware)': sample_ave})

            # add to all connections list
            conn.append(subconn)

        return tuple(conn)

    def _get_dset_shape(self, config_name, adc, conn_tuple):
        conn = conn_tuple

        # gather all dataset shapes
        brd = conn[0]
        dset_shapes = []
        for ch in conn[1]:
            dset_name = self.construct_dataset_name(
                brd, ch,
                config_name=config_name,
                adc=adc,
                silent=True
            )
            dset_shapes.append(self.group[dset_name].shape)

        # check all datasets have the same shape
        if all(shape == dset_shapes[0] for shape in dset_shapes):
            # all shapes are consistent
            if len(dset_shapes[0]) == 1:
                nshotnum = 1
                nt = dset_shapes[0][0]
            else:
                nshotnum = dset_shapes[0][0]
                nt = dset_shapes[0][1]
        else:
            raise ValueError(
                'Dataset shapes on board {} are not'.format(
                    brd)
                + ' consistent adc ({})'.format(adc))

        # return
        return nshotnum, nt

    def _parse_config_name(self, name: str) -> Union[None, str]:
        """
        Parses :code:`name` to determine the digitizer configuration
        name.  A configuration group name follows the format::

            '<configuration name>'

        :param name: name of potential configuration group
        :returns: digitizer configuration name, or :code:`None` if
            `name` does not represent a configuration group

        .. note::

            The group is only considered a configuration group if it
            contains the attributes :ibf:`'SIS crate board types'`,
            :ibf:`'SIS crate config indices'`, and
            :ibf:`'SIS crate slot numbers'`
        """
        expected_attrs = ('SIS crate board types',
                          'SIS crate config indices',
                          'SIS crate slot numbers')
        if name not in self.group:
            return
        elif not isinstance(self.group[name], h5py.Group):
            return
        elif all(attr in self.group[name].attrs
                 for attr in expected_attrs):
            return name
        else:
            return

    @staticmethod
    def brd_to_slot(brd, adc):
        """
        Translates board number and adc name to the digitizer slot
        number.

        :param int brd: board number
        :param str adc: adc name
        :return: digitizer slot number
        :rtype: int
        """
        bs_map = {(1, 'SIS 3302'): 5,
                  (2, 'SIS 3302'): 7,
                  (3, 'SIS 3302'): 9,
                  (4, 'SIS 3302'): 11,
                  (1, 'SIS 3305'): 13,
                  (2, 'SIS 3305'): 15}
        return bs_map[(brd, adc)]

    def construct_dataset_name(self, board, channel,
                               config_name=None, adc=None,
                               return_info=False, silent=False):
        """
        Constructs the HDF5 dataset name based on inputs.  The dataset
        name follows the format:

            | `config_name` [Slot `#`: SIS `####` FPGA `#` ch `#`]

        (See
        :meth:`~.templates.HDFMapDigiTemplate.construct_dataset_name`
        of the base class for details)
        """
        # TODO: Replace Warnings with proper error handling

        # initiate warning string
        warn_str = ''

        # Condition config_name
        # - if config_name is not specified then the 'active' config
        #   is sought out
        if config_name is None:
            found = 0
            for name in self._configs:
                if self._configs[name]['active'] is True:
                    config_name = name
                    found += 1

            if found == 1:
                warn_str = ('\nconfig_name not specified, '
                            'assuming ' + config_name + '.')
            elif found >= 1:
                raise ValueError("There are multiple active digitizer"
                                 "configurations. User must specify"
                                 "config_name keyword.")
            else:
                raise ValueError("No active digitizer configuration "
                                 "detected.")
        elif config_name not in self._configs:
            # config_name must be a known configuration
            raise ValueError('Invalid configuration name given.')
        elif self._configs[config_name]['active'] is False:
            raise ValueError('Specified configuration name is not '
                             'active.')

        # Condition adc
        # - if adc is not specified then the slow adc '3302' is assumed
        #   or, if 3305 is the only active adc, then it is assumed
        # - self.__config_crates() always adds 'SIS 3302' first. If
        #   '3302' is not active then the list will only contain '3305'.
        if adc is None:
            adc = self._configs[config_name]['adc'][0]
            warn_str += '\nNo adc specified, so assuming ' + adc + '.'
        elif adc not in self._configs[config_name]['adc']:
            raise ValueError(
                'Specified adc ({}) is not in specified '.format(adc)
                + 'configuration ({}).'.format(config_name))

        # search if (board, channel) combo is connected
        bc_valid = False
        d_info = None
        for brd, chs, extras in self._configs[config_name][adc]:
            if board == brd:
                if channel in chs:
                    bc_valid = True

                    # save adc settings for return if requested
                    d_info = extras
                    d_info['adc'] = adc
                    d_info['configuration name'] = config_name
                    d_info['digitizer'] = self._info['group name']

        # (board, channel) combo must be active
        if bc_valid is False:
            raise ValueError('Specified (board, channel) is not valid')

        # checks passed, build dataset_name
        if '3302' in adc:
            slot = self.brd_to_slot(board, 'SIS 3302')
            dataset_name = '{0} [Slot {1}: SIS 3302 ch {2}]'.format(
                config_name, slot, channel)
        elif '3305' in adc:
            slot = self.brd_to_slot(board, 'SIS 3305')
            if channel in range(1, 5):
                fpga = 1
                ch = channel
            else:
                fpga = 2
                ch = channel - 4

            dataset_name = '{0} [Slot {1}: '.format(config_name, slot) \
                           + 'SIS 3305 FPGA {0} ch {1}]'.format(fpga,
                                                                ch)
        else:
            raise ValueError('We have a problem! Somehow adc '
                             + '({}) is not known.'.format(adc))

        # print warnings
        if not silent and warn_str != '':
            warn(warn_str)

        # return
        if return_info is True:
            return dataset_name, d_info
        else:
            return dataset_name

    def construct_header_dataset_name(self, board, channel, **kwargs):
        """"Name of header dataset"""
        # ensure return_info kwarg is always False
        kwargs['return_info'] = False

        # get dataset naem
        dset_name = self.construct_dataset_name(board, channel,
                                                **kwargs)
        # build and return header name
        dheader_name = dset_name + ' headers'
        return dheader_name

    @staticmethod
    def slot_to_brd(slot):
        """
        Translates the 'SIS crate` slot number to the board number and
        adc.

        :param int slot: digitizer slot number
        :return: (board number, adc name)
        :rtype: (int, str)
        """
        sb_map = {5: (1, 'SIS 3302'),
                  7: (2, 'SIS 3302'),
                  9: (3, 'SIS 3302'),
                  11: (4, 'SIS 3302'),
                  13: (1, 'SIS 3305'),
                  15: (2, 'SIS 3305')}
        return sb_map[slot]
