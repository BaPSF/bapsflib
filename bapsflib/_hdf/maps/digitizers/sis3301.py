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
Module for the SIS3301 digitizer mapper
`~bapsflib._hdf.maps.digitizers.sis3301.HDFMapDigiSIS3301`.
"""
__all__ = ["HDFMapDigiSIS3301"]

import astropy.units as u
import h5py
import numpy as np
import os
import re

from typing import Any, Dict, Tuple, Union
from warnings import warn

from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate
from bapsflib.utils import _bytes_to_str
from bapsflib.utils.exceptions import HDFMappingError


class HDFMapDigiSIS3301(HDFMapDigiTemplate):
    """
    Mapping class for the 'SIS 3301' digitizer.

    Simple group structure looks like:

    .. code-block:: none

        +-- SIS 3301
        |   +-- Config01 [0:0]
        |   +-- Config01 [0:0] headers
        .
        .
        .
        |   +-- Configuration: Config01
        |   |   +-- Boards[0]
        |   |   |   +-- Channels[0]
        |   |   |   |   +--
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
        self._device_adcs = ("SIS 3301",)  # type: Tuple[str, ...]

        # populate self.configs
        self._build_configs()

    def _adc_info_first_pass(
        self, adc_name: str, config_group: h5py.Group
    ) -> Tuple[Tuple[int, Tuple[int, ...], Dict[str, Any]], ...]:
        """
        Gathers the analog-digital-converter's connected board and
        channel numbers, as well as, the associated setup configuration
        for each connected board.

        :param adc_name: name of analog-digital-converter
        :param config_group: HDF5 group object of the configuration
            group

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
        # 'Raw data + config/SIS 3301' group has only one possible
        # adc ('SIS 3301')
        # adc_info = (
        #     int, # board number
        #     (int, ...), # connected channel numbers
        #     {'bit': 14, # bit resolution
        #      'clock rate': <Quantity 100.0 MHz>,
        #      'nshotnum': int,
        #      'shot average (software)': int,
        #      'sample average (hardware)': int})
        #
        # initialize
        adc_info = []

        # conns is a tuple of tuples where each tuple is a seed for the
        # elements of `adc_info`
        conns = self._find_adc_connections(adc_name, config_group)

        for conn in conns:
            # define 'bit' and 'clock rate'
            conn[2]["bit"] = 14
            conn[2]["clock rate"] = u.Quantity(100.0, unit="MHz")

            # add 'shot average (software)' to dict
            if "Shots to average" in config_group.attrs:
                shtave = config_group.attrs["Shots to average"]
                if shtave == 0 or shtave == 1:
                    shtave = None
            else:
                shtave = None
            conn[2]["shot average (software)"] = shtave

            # add 'sample average (hardware)' to dict
            splave = None
            avestr = ""
            find_splave = False
            if "Samples to average" in config_group.attrs:
                avestr = config_group.attrs["Samples to average"]
                avestr = _bytes_to_str(avestr)
                find_splave = True
            elif "Unnamed" in config_group.attrs:
                avestr = config_group.attrs["Unnamed"]
                try:
                    avestr = _bytes_to_str(avestr)
                    find_splave = True
                except TypeError:
                    avestr = ""
                    find_splave = False

            if find_splave:
                if avestr != "No averaging":
                    _match = re.fullmatch(
                        r"(\bAverage\s)(?P<NAME>.+)(\sSamples\b)", avestr
                    )
                    if bool(_match):
                        try:
                            # splave = int(avestr.split()[1])
                            splave = int(_match.group("NAME"))

                            if splave == 0 or splave == 1:
                                splave = None
                        except ValueError:
                            warn(
                                f"Found sample averaging of '{_match.group('NAME')}' "
                                f"but can not convert to int...using a value of "
                                f"None instead"
                            )
            conn[2]["sample average (hardware)"] = splave

            # append info
            adc_info.append(conn)

        return tuple(adc_info)

    def _adc_info_second_pass(
        self, config_name: str, adc_name: str
    ) -> Tuple[Tuple[int, Tuple[int, ...], Dict[str, Any]], ...]:
        """
        Reviews and updates the `adc_info` originally generated by
        :meth:`_adc_info_first_pass`.

        :param config_name: digitizer configuration name
        :param adc_name: name of analog-digital-converter

        :return:

            Tuple of 3-element tuples where the 1st element of the
            nested tuple represents a connected *board* number, the 2nd
            element is a tuple of connected *channel* numbers for the
            *board*, and the 3rd element is a dictionary of adc setup
            values (*bit*, *clock rate*, etc.).

        On the second pass, the main and header dataset associated with
        each board number and channel number is reviewed.  The
        meta-info dict is then updated with:

        .. csv-table::
            :header: "Key", "Description"
            :widths: 20, 60

            "::

                'nshotnum'
            ", "
            the number of shot numbers contained in the datasets
            associated with a **board**, equivalent to
            :code:`dset.shape[0]`
            "
            "::

                'nt'
            ", "
            the number of time samples recorded in the datasets
            associated with a **board**, equivalent to
            :code:`dset.shape[1]`
            "
        """
        # ensure dataset exists for each (brd, ch) combo
        # - remove (brd, ch) combos if dataset does not exist
        # - remove brd entry if chs are NULL
        # populate 'nshotnum' and 'nt' for each board
        # - confirm all associated channels have matching shape
        # - if not, then define nshotnum = 0 and nt = 0 and warn
        #
        # get conns
        conns = self.configs[config_name][adc_name]
        new_conns = []

        # review connections
        for iconn, conn in enumerate(conns):
            brd = conn[0]
            chs = conn[1]

            # look for dataset existence
            new_chs = list(chs)
            chs_to_remove = []
            for ch in chs:
                # get datasets
                names = [
                    self.construct_dataset_name(brd, ch, config_name=config_name),
                    self.construct_header_dataset_name(brd, ch, config_name=config_name),
                ]
                for dset_name in names:
                    if dset_name not in self.group:
                        why = (
                            f"HDF5 structure unexpected...dataset '{dset_name}' "
                            f"not found for board {brd} and channel {ch}"
                            f"...removing combo from map"
                        )
                        warn(why)
                        chs_to_remove.append(ch)

            # ensure chs is not NULL
            chs_to_remove = list(set(chs_to_remove))
            for ch in chs_to_remove:
                new_chs.remove(ch)
            if len(new_chs) == 0:
                why = (
                    f"HDF5 structure unexpected...'Board number {brd}' does not "
                    f"define any valid channel numbers...not adding to "
                    f"`configs` dict"
                )
                warn(why)

                # skip adding to conn list
                continue

            # get 'nshotnum' and 'nt' values
            chs_to_remove = []
            nshotnum = None
            nt = None
            for ch in new_chs:
                # -- examine dataset --
                dset_name = self.construct_dataset_name(brd, ch, config_name=config_name)
                dset = self.group[dset_name]

                # dataset should not have fields
                if dset.dtype.names is not None:
                    why = (
                        f"HDF5 structure unexpected...dataset '{dset_name}' has "
                        f"fields...not adding to `configs` dict"
                    )
                    warn(why)
                    chs_to_remove.append(ch)
                    continue

                # dataset should be a 2D array
                if len(dset.shape) != 2:
                    # dataset not 2D array
                    why = (
                        f"HDF5 structure unexpected...dataset '{dset_name}' is "
                        f"NOT a 2D array...not adding to `configs` dict"
                    )
                    warn(why)
                    chs_to_remove.append(ch)
                    continue

                # Define and check nt
                # - should be consistent across all datasets
                if nt is None:
                    nt = dset.shape[1]
                elif nt == -1:
                    pass
                else:
                    if nt != dset.shape[1]:
                        why = (
                            f"HDF5 structure unexpected...number of time "
                            f"sample inconsistent across all channels for "
                            f"board {brd}...setting nt = -1"
                        )
                        warn(why)
                        nt = -1
                        continue

                # Define and check nshotnum
                # - should be consistent across all datasets
                if nshotnum is None:
                    nshotnum = dset.shape[0]
                elif nshotnum == -1:
                    pass
                else:
                    if nshotnum != dset.shape[0]:
                        why = (
                            f"HDF5 structure unexpected...number of shot "
                            f"numbers inconsistent across all channels for "
                            f"board {brd}...setting nshotnum = -1"
                        )
                        warn(why)
                        nshotnum = -1
                        continue

                # -- examine header dataset --
                hdset_name = self.construct_header_dataset_name(
                    brd, ch, config_name=config_name
                )
                hdset = self.group[hdset_name]
                sn_field = self.configs[config_name]["shotnum"]["dset field"][0]

                # should have fields (specifically the shotnum field)
                if sn_field not in hdset.dtype.names:
                    if "Shot number" in hdset.dtype.names and iconn == 0:
                        sn_field = "Shot number"
                        self.configs[config_name]["shotnum"]["dset field"] = (
                            "Shot number",
                        )
                    else:
                        why = (
                            f"HDF5 structure unexpected...dataset '{hdset_name}' "
                            f"does NOT have expected shot number field "
                            f"'{sn_field}'...not adding to `configs` dict"
                        )
                        warn(why)
                        chs_to_remove.append(ch)
                        continue

                # shot number has incorrect shape and type
                if hdset.dtype[sn_field].shape != () or not np.issubdtype(
                    hdset.dtype[sn_field], np.integer
                ):
                    why = (
                        f"HDF5 structure unexpected...dataset '{hdset_name}' "
                        f"does NOT have expected shape and dtype for a shot "
                        f"numbers...not adding to `configs` dict"
                    )
                    warn(why)
                    chs_to_remove.append(ch)
                    continue

                # both datasets (main and header) should have same
                # number of shot numbers
                if dset.shape[0] != hdset.shape[0]:
                    why = (
                        f"HDF5 structure unexpected...dataset and header "
                        f"dataset for board {brd} and channel {ch} do NOT have "
                        f"the same number of shot numbers...not adding to "
                        f"`configs` dict"
                    )
                    warn(why)
                    chs_to_remove.append(ch)
                    continue

            # ensure chs is not NULL
            for ch in chs_to_remove:
                new_chs.remove(ch)
            if len(new_chs) == 0:
                why = (
                    f"HDF5 structure unexpected...'Board number {brd}' does not "
                    f"define any valid channel numbers...not adding to "
                    f"`configs` dict"
                )
                warn(why)

                # skip adding to conn list
                continue

            # add nshotnum and nt to setup dict
            conn[2].update(
                {
                    "nshotnum": nshotnum,
                    "nt": nt,
                }
            )
            # append new_conns
            new_conns.append((brd, tuple(new_chs), conn[2]))

        return tuple(new_conns)

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
                    "config group path": self.group[name].name,
                }

                # determine if config is active
                self._configs[config_name]["active"] = self.deduce_config_active_status(
                    config_name
                )

                # assign active adc's to the configuration
                self._configs[config_name]["adc"] = self._find_active_adcs(
                    self.group[name]
                )

                # define 'shotnum' entry
                #
                # Note:
                #   The original dataset shot number field was named
                #   'Shot'.  At some point (mid- to late- 00's) this
                #   field was renamed to 'Shot number'.
                #
                #   When the header dataset is reviewed by
                #   `_adc_info_second_pass()` the field name will be
                #   changed when appropriate.
                #
                self._configs[config_name]["shotnum"] = {
                    "dset field": ("Shot",),
                    "shape": (),
                    "dtype": np.uint32,
                }

                # initialize adc info
                self._configs[config_name]["SIS 3301"] = self._adc_info_first_pass(
                    "SIS 3301", self.group[name]
                )

                # update adc info with 'nshotnum' and 'nt'
                # - `construct_dataset_name` needs adc info to be seeded
                # - the following updates depend on
                #   construct_dataset_name
                #
                if self._configs[config_name]["active"]:
                    self._configs[config_name]["SIS 3301"] = self._adc_info_second_pass(
                        config_name, "SIS 3301"
                    )
                else:
                    for conn in self._configs[config_name]["SIS 3301"]:
                        conn[2].update(
                            {
                                "nshotnum": -1,
                                "nt": -1,
                            }
                        )

        # -- raise HDFMappingErrors                                 ----
        # no configurations found
        if not bool(self._configs):
            why = "there are no mappable configurations"
            raise HDFMappingError(self.info["group path"], why=why)

        # ensure there are active configs
        if len(self.active_configs) == 0:
            raise HDFMappingError(
                self.info["group path"], "there are not active configurations"
            )

        # ensure active configs are not NULL
        for config_name in self.active_configs:
            config = self.configs[config_name]
            if len(config["SIS 3301"]) == 0:
                raise HDFMappingError(
                    self.info["group path"],
                    f"active configuration '{config_name}' has no connected "
                    f"board and channels",
                )

    @staticmethod
    def _find_active_adcs(config_group: h5py.Group) -> Tuple[str, ...]:
        """
        Determines active adc's used in the digitizer configuration.

        :param config_group: HDF5 group object of the configuration
            group

        :returns: tuple of active (used) analog-digital-converter names
        """
        # noinspection PyRedundantParentheses
        return ("SIS 3301",)

    def _find_adc_connections(
        self, adc_name: str, config_group: h5py.Group
    ) -> Tuple[Tuple[int, Tuple[int, ...], Dict[str, Any]], ...]:
        """
        Determines active connections on the adc.

        :param adc_name: name of the analog-digital-converter
        :param config_group: HDF5 group object of the configuration
            group

        :return:

            Tuple of 3-element tuples where the 1st element of the
            nested tuple represents a connected *board* number, the 2nd
            element is a tuple of connected *channel* numbers for the
            *board*, and the 3rd element is a dictionary of adc setup
            values (*bit*, *clock rate*, etc.).
        """
        config_name = self._parse_config_name(os.path.basename(config_group.name))
        active = self.deduce_config_active_status(config_name)

        # initialize conn, brd, and chs
        # conn = list of connections
        # brd  = board number
        # chs  = list of connect channels of board brd
        #
        conn = []

        # Determine connected (brd, ch) combinations
        # scan thru board groups
        for board in config_group:
            # Is it a board group?
            if not bool(re.fullmatch(r"Boards\[\d+\]", board)):
                warn(
                    f"'{board}' does not match expected board group name..."
                    f"not adding to mapping"
                )
                continue

            # get board number
            brd_group = config_group[board]
            try:
                brd = brd_group.attrs["Board"]
            except KeyError:
                raise HDFMappingError(
                    self.info["group path"], "board number attribute 'Board' missing"
                )

            # ensure brd is an int
            if not isinstance(brd, (int, np.integer)):
                warn("Board number is not an integer")
                continue
            elif brd < 0:
                warn("Board number is less than 0.")
                continue

            # ensure there's no duplicate board numbers
            if brd in [sconn[0] for sconn in conn]:
                why = (
                    f"HDF5 structure unexpected...'{config_group.name}' defines "
                    f"duplicate board numbers"
                )

                # error if active, else warn
                if active:
                    raise HDFMappingError(self.info["group path"], why=why)
                else:
                    warn(why)

                    # skip adding to conn list
                    continue

            # scan thru channel groups
            chs = []
            for ch_key in brd_group:
                # Is it a channel group?
                if not bool(re.fullmatch(r"Channels\[\d+\]", ch_key)):
                    warn(
                        f"'{board}' does not match expected channel group name"
                        f"...not adding to mapping"
                    )
                    continue

                # get channel number
                ch_group = brd_group[ch_key]
                try:
                    ch = ch_group.attrs["Channel"]
                except KeyError:
                    raise HDFMappingError(
                        self.info["group path"],
                        "Channel number attribute 'Channel' missing",
                    )

                # ensure ch is an int
                if not isinstance(ch, (int, np.integer)):
                    warn("Channel number is not an integer")
                    continue
                elif ch < 0:
                    warn("Channel number is less than 0.")
                    continue

                # define list of channels
                chs.append(ch)

            # ensure connected channels are unique
            if len(chs) != len(set(chs)):
                why = (
                    f"HDF5 structure unexpected...'{brd_group.name}' does not "
                    f"define a unique set of channel numbers...not adding to "
                    f"`configs` dict"
                )
                warn(why)

                # skip adding to conn list
                continue

            # ensure chs is not NULL
            if len(chs) == 0:
                why = (
                    f"HDF5 structure unexpected...'{brd_group.name}' does not "
                    f"define any valid channel numbers...not adding to "
                    f"`configs` dict"
                )
                warn(why)

                # skip adding to conn list
                continue

            # build subconn tuple with connected board, channels, and
            # acquisition parameters
            subconn = (brd, tuple(chs), {"bit": None, "clock rate": (None, "MHz")})

            # add to all connections list
            conn.append(subconn)

        return tuple(conn)

    @staticmethod
    def _parse_config_name(name: str) -> Union[None, str]:
        """
        Parses :code:`name` to determine the digitizer configuration
        name.  A configuration group name follows the format::

            'Configuration: <configuration name>'

        :param name: name of potential configuration group
        :returns: digitizer configuration name, or :code:`None` if
            `name` does not represent a configuration group
        """
        # Define RE pattern
        # - A configuration group follows the naming scheme of:
        #
        #     'Configuration: <NAME>'
        #
        #   where <NAME> is the configuration name
        #
        _pattern = r"(\bConfiguration:\s)(?P<NAME>.+\b)"

        # match _pattern against gname
        _match = re.fullmatch(_pattern, name)

        # return configuration name
        if bool(_match):
            # full match successful
            return _match.group("NAME")
        else:
            return

    def construct_dataset_name(
        self,
        board: int,
        channel: int,
        config_name=None,
        adc="SIS 3301",
        return_info=False,
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Construct the name of the HDF5 dataset containing digitizer
        data. The dataset name follows the format::

            '<config_name> [<board>:<channel>]'

        where `<config_name>` is the digitizer configuration name,
        `<board>` is the requested board number, and `<channel>` is
        the requested channel number.

        :param board: board number
        :param channel: channel number
        :param str config_name: digitizer configuration name
        :param str adc: analog-digital-converter name
        :param bool return_info: :code:`True` will return a dictionary
            of meta-info associated with the digitizer data
            (DEFAULT :code:`False`)
        :returns: digitizer dataset name. If :code:`return_info=True`,
            then returns a tuple of (dataset name, dictionary of
            meta-info)

        The returned adc information dictionary looks like::

            adc_dict = {
                'adc': str,
                'bit': int,
                'clock rate': astropy.units.Quantity,
                'configuration name': str,
                'digitizer': str,
                'nshotnum': int,
                'nt': int,
                'sample average (hardware)': int,
                'shot average (software)': int,
            }
        """
        # Condition config_name
        # - if config_name is not specified then the 'active' config
        #   is sought out
        if config_name is None:
            if len(self.active_configs) == 1:
                config_name = self.active_configs[0]
                warn(f"`config_name` not specified, assuming '{config_name}'.")
            elif len(self.active_configs) > 1:
                raise ValueError(
                    "There are multiple active digitizer "
                    "configurations...`config_name` kwarg must be "
                    "specified."
                )
            else:
                raise ValueError("No active digitizer configuration detected.")
        elif config_name not in self._configs:
            # config_name must be a known configuration
            raise ValueError("Invalid `config_name` given.")
        elif self._configs[config_name]["active"] is False:
            raise ValueError("Specified configuration name `config_name` is not active.")

        # Condition adc keyword
        if adc != "SIS 3301":
            raise ValueError(
                f"Specified adc ({adc}) is not in specified configuration "
                f"({config_name})."
            )

        # search if (board, channel) combo is connected
        bc_valid = False
        d_info = None
        for brd, chs, extras in self._configs[config_name]["SIS 3301"]:
            if board == brd and channel in chs:
                # board, channel combo valid
                bc_valid = True

                # save adc settings for return if requested
                if return_info:
                    d_info = extras
                    d_info["adc"] = "SIS 3301"
                    d_info["configuration name"] = config_name
                    d_info["digitizer"] = self._info["group name"]
                break

        # (board, channel) combo must be active
        if not bc_valid:
            raise ValueError(
                "Input `board` and `channel` do NOT specified a valid dataset."
            )

        # checks passed, build dataset_name
        dataset_name = f"{config_name} [{board}:{channel}]"

        # return
        if return_info is True:
            return dataset_name, d_info
        else:
            return dataset_name

    def construct_header_dataset_name(
        self, board: int, channel: int, config_name=None, adc="SIS 3301", **kwargs
    ) -> str:
        """
        Construct the name of the HDF5 header dataset associated with
        the digitizer dataset. The header dataset stores shot numbers
        and other shot number specific meta-data.  It also has a one-
        to-one row correspondence with the digitizer dataset.  The
        header dataset name follows the format::

            '<dataset name> headers'

        where `<dataset name>` is the digitizer dataset name specified
        by the input arguments and constructed by
        :meth:`construct_dataset_name`.

        :param board: board number
        :param channel: channel number
        :param str config_name: digitizer configuration name
        :param str adc: analog-digital-converter name
        :returns: header dataset name associated with the digitizer
            dataset
        """
        # ensure return_info kwarg is always False
        kwargs["return_info"] = False

        # get dataset name
        dset_name = self.construct_dataset_name(
            board, channel, config_name=config_name, adc=adc, **kwargs
        )

        # build and return header name
        dheader_name = f"{dset_name} headers"
        return dheader_name
