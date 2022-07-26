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
Module for the "SIS crate" digitizer mapper
`~bapsflib._hdf.maps.digitizers.siscrate.HDFMapDigiSISCrate`.
"""
__all__ = ["HDFMapDigiSISCrate"]

import astropy.units as u
import h5py
import numpy as np
import re

from typing import Any, Dict, Tuple, Union
from warnings import warn

from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate
from bapsflib.utils.exceptions import HDFMappingError


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
        self._device_adcs = (
            "SIS 3302",
            "SIS 3305",
        )  # type: Tuple[str, ...]

        # populate self.configs
        self._build_configs()

    def _adc_info_first_pass(
        self, config_name: str, adc_name: str
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
            if adc_name == "SIS 3302":
                conn[2]["bit"] = 16
            else:
                # * this is the adc_name == 'SIS 3305' case
                # * `_find_adc_connections() ensures only 'SIS 3302'
                #   and 'SIS 3305' can come out
                conn[2]["bit"] = 10

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
        for conn in conns:
            brd = conn[0]
            chs = conn[1]

            # look for dataset existence
            new_chs = list(chs)
            chs_to_remove = []
            for ch in chs:
                # get datasets
                names = [
                    self.construct_dataset_name(
                        brd, ch, config_name=config_name, adc=adc_name
                    ),
                    self.construct_header_dataset_name(
                        brd, ch, config_name=config_name, adc=adc_name
                    ),
                ]
                for dset_name in names:
                    if dset_name not in self.group:
                        why = (
                            f"HDF5 structure unexpected...dataset '{dset_name}' "
                            f"not found for board {brd} and channel {ch}..."
                            f"removing combo from map"
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
                    f"define any valid channel numbers...not adding to `configs` "
                    f"dict"
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
                dset_name = self.construct_dataset_name(
                    brd, ch, config_name=config_name, adc=adc_name
                )
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
                            f"HDF5 structure unexpected...number of time sample "
                            f"inconsistent across all channels for board {brd}..."
                            f"setting nt = -1"
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
                            f"HDF5 structure unexpected...number of shot numbers "
                            f"inconsistent across all channels for board {brd}..."
                            f"setting nshotnum = -1"
                        )
                        warn(why)
                        nshotnum = -1
                        continue

                # -- examine header dataset --
                hdset_name = self.construct_header_dataset_name(
                    brd, ch, config_name=config_name, adc=adc_name
                )
                hdset = self.group[hdset_name]
                sn_field = self.configs[config_name]["shotnum"]["dset field"][0]

                # should have fields (specifically the shotnum field)
                if sn_field not in hdset.dtype.names:
                    why = (
                        f"HDF5 structure unexpected...dataset '{hdset_name}' does "
                        f"NOT have expected shot number field '{sn_field}'..."
                        f"not adding to `configs` dict"
                    )
                    warn(why)
                    chs_to_remove.append(ch)
                    continue

                # shot number has incorrect shape and type
                if hdset.dtype[sn_field].shape != () or not np.issubdtype(
                    hdset.dtype[sn_field], np.integer
                ):
                    why = (
                        f"HDF5 structure unexpected...dataset '{hdset_name}' does "
                        f"NOT have expected shape and dtype for a shot numbers"
                        f"...not adding to `configs` dict"
                    )
                    warn(why)
                    chs_to_remove.append(ch)
                    continue

                # both datasets (main and header) should have same
                # number of shot numbers
                if dset.shape[0] != hdset.shape[0]:
                    why = (
                        f"HDF5 structure unexpected...dataset and header dataset "
                        f"for board {brd} and channel {ch} do NOT have th same "
                        f"number of shot numbers...not adding to `configs` dict"
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
                self._configs[config_name]["shotnum"] = {
                    "dset field": ("Shot number",),
                    "shape": (),
                    "dtype": np.uint32,
                }

                # initialize adc info
                for adc in self._configs[config_name]["adc"]:
                    self._configs[config_name][adc] = self._adc_info_first_pass(
                        config_name, adc
                    )

                # update adc info with 'nshotnum' and 'nt'
                # - `construct_dataset_name` needs adc info to be seeded
                # - the following updates depend on
                #   construct_dataset_name
                #
                for adc in self._configs[config_name]["adc"]:
                    if self._configs[config_name]["active"]:
                        self._configs[config_name][adc] = self._adc_info_second_pass(
                            config_name, adc
                        )
                    else:
                        for conn in self._configs[config_name][adc]:
                            conn[2].update(
                                {
                                    "nshotnum": -1,
                                    "nt": -1,
                                }
                            )
                """
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
                """

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
        for config_name in self.active_configs:  # pragma: no branch
            config = self.configs[config_name]
            if len(config["adc"]) == 0:
                raise HDFMappingError(
                    self.info["group path"],
                    f"active configuration '{config_name}' has no active adc's",
                )

            adcs = list(config["adc"])
            for adc in config["adc"]:  # pragma: no branch
                if len(config[adc]) == 0:  # pragma: no branch
                    del config[adc]
                    adcs.remove(adc)
            if len(adcs) == 0:
                raise HDFMappingError(
                    self.info["group path"],
                    f"active configuration '{config_name}' has no mapped "
                    f"connections for any adc",
                )
            else:
                config["adc"] = tuple(adcs)

    @staticmethod
    def _find_active_adcs(config_group: h5py.Group) -> Tuple[str, ...]:
        """
        Determines active adc's used in the digitizer configuration.

        :param config_group: HDF5 group object of the configuration
            group

        :returns: tuple of active (used) analog-digital-converter names
        """
        active_adcs = []
        adc_types = config_group.attrs["SIS crate board types"]
        if 2 in adc_types:
            active_adcs.append("SIS 3302")
        if 3 in adc_types:
            active_adcs.append("SIS 3305")

        return tuple(active_adcs)

    def _find_adc_connections(
        self, adc_name: str, config_name: str
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
        config_path = self.configs[config_name]["config group path"]
        config_group = self.group.get(config_path)
        active = self.configs[config_name]["active"]

        # initialize conn
        # conn = list of connections
        #
        conn = []

        # define _helpers
        if adc_name not in ("SIS 3302", "SIS 3305"):  # pragma: no cover
            # this should never happen
            warn(f"Invalid adc name '{adc_name}'")
            return ()
        _helpers = {
            "SIS 3302": {
                "short": "3302",
                "re": r"SIS crate 3302 configurations\[(?P<INDEX>\d+)\]",
            },
            "SIS 3305": {
                "short": "3305",
                "re": r"SIS crate 3305 configurations\[(?P<INDEX>\d+)\]",
            },
        }

        # get slot numbers and configuration indices
        slots = config_group.attrs["SIS crate slot numbers"]  # type: np.ndarray
        indices = config_group.attrs["SIS crate config indices"]  # type: np.ndarray

        # ensure slots and indices are 1D arrays of the same size
        if slots.ndim != 1 or indices.ndim != 1:
            raise HDFMappingError(
                self.info["group path"],
                "HDF5 structure unexpected...Defined slots and "
                "configuration indices are not 1D arrays.",
            )
        elif slots.size != indices.size:
            raise HDFMappingError(
                self.info["group path"],
                "HDF5 structure unexpected...Defined slots and "
                "configuration indices are not the same size.",
            )

        # ensure defined slots are unique
        if np.unique(slots).size != slots.size:
            raise HDFMappingError(
                self.info["group path"],
                "HDF5 structure unexpected...defined slot numbers are not unique",
            )

        # Build tuple (slot, config index, board, adc)
        # - build a tuple that pairs the adc name (adc), adc slot
        #   number (slot), configuration group index (index), and
        #   board number (brd)
        #
        adc_pairs = []
        for slot, index in zip(slots, indices):
            if slot != 3:
                try:
                    brd, adc = self.slot_info[slot]
                    adc_pairs.append((slot, index, brd, adc))
                except KeyError:
                    why = (
                        f"HDF5 structure unexpected...defined slot number {slot} "
                        f"is unexpected...not adding to `configs` mapping"
                    )
                    warn(why)

        # Ensure the same configuration index is not assign to multiple
        # slots for the same adc
        for slot, index, brd, adc in adc_pairs:
            for ss, ii, bb, aa in adc_pairs:
                if ii == index and aa == adc and ss != slot:
                    why = (
                        "The same configuration index is assigned "
                        "to multiple slots of the same adc."
                    )
                    if active:
                        raise HDFMappingError(self.info["group path"], why=why)
                    else:
                        why += "...config not active so not adding to mapping"
                        warn(why)
                        return ()

        # gather adc configuration groups
        gnames = []
        for name in config_group:
            _match = re.fullmatch(_helpers[adc_name]["re"], name)
            if bool(_match):
                gnames.append((name, int(_match.group("INDEX"))))

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
                why = (
                    f"Board not found since group name determined "
                    f"`config_index` {config_index} not defined in top-level "
                    f"configuration group"
                )
                warn(why)
                continue

            # find connected channels
            chs = []
            if adc_name == "SIS 3302":
                _patterns = (r"Enabled\s(?P<CH>\d+)",)
            else:
                # SIS 3305
                _patterns = (
                    r"FPGA 1 Enabled\s(?P<CH>\d+)",
                    r"FPGA 2 Enabled\s(?P<CH>\d+)",
                )
            for key, val in config_group[name].attrs.items():
                if "Enabled" in key and val == b"TRUE":
                    ch = None
                    for pat in _patterns:
                        _match = re.fullmatch(pat, key)
                        if bool(_match):
                            ch = int(_match.group("CH"))
                            if "FPGA 2" in pat:
                                ch += 4
                            break

                    if ch is not None:
                        chs.append(ch)

            # ensure chs is not NULL
            if len(chs) == 0:
                why = (
                    f"HDF5 structure unexpected...'{config_name}/{name}' does "
                    f"not define any valid channel numbers...not adding to "
                    f"`configs` dict"
                )
                warn(why)

                # skip adding to conn list
                continue

            # determine shot averaging
            shot_ave = None
            if "Shot averaging (software)" in config_group[name].attrs:
                shot_ave = config_group[name].attrs["Shot averaging (software)"]
                if shot_ave in (0, 1):
                    shot_ave = None

            # determine sample averaging
            sample_ave = None
            if adc_name == "SIS 3305":
                # the 'SIS 3305' adc does NOT support sample averaging
                pass
            else:
                # SIS 3302
                # - the HDF5 attribute is the power to 2
                # - So, a hardware sample of 5 actually means the number
                #   of points sampled is 2^5
                if "Sample averaging (hardware)" in config_group[name].attrs:
                    sample_ave = config_group[name].attrs["Sample averaging (hardware)"]
                    if sample_ave == 0:
                        sample_ave = None
                    else:
                        sample_ave = 2**sample_ave

            # determine clock rate
            if adc_name == "SIS 3305":
                # has different clock rate modes
                try:
                    cr_mode = config_group[name].attrs["Channel mode"]
                    cr_mode = int(cr_mode)
                except (KeyError, ValueError):
                    why = (
                        f"HDF5 structure unexpected...'{config_name}/{name}' does "
                        f"not define a clock rate mode...setting to None in the "
                        f"`configs` dict"
                    )
                    warn(why)
                    cr_mode = -1
                if cr_mode == 0:
                    cr = u.Quantity(1.25, unit="GHz")
                elif cr_mode == 1:
                    cr = u.Quantity(2.5, unit="GHz")
                elif cr_mode == 2:
                    cr = u.Quantity(5.0, unit="GHz")
                else:
                    cr = None
            else:
                # 'SIS 3302' has one clock rate mode
                cr = u.Quantity(100.0, unit="MHz")

            # build subconn tuple with connected board, channels, and
            # acquisition parameters
            subconn = (
                brd,
                tuple(chs),
                {
                    "clock rate": cr,
                    "shot average (software)": shot_ave,
                    "sample average (hardware)": sample_ave,
                },
            )

            # add to all connections list
            conn.append(subconn)

        return tuple(conn)

    """
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
    """

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
        expected_attrs = (
            "SIS crate board types",
            "SIS crate config indices",
            "SIS crate slot numbers",
        )
        if name not in self.group:
            return
        elif not isinstance(self.group[name], h5py.Group):
            return
        elif all(attr in self.group[name].attrs for attr in expected_attrs):
            return name
        else:
            return

    def construct_dataset_name(
        self, board: int, channel: int, config_name=None, adc=None, return_info=False
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Construct the name of the HDF5 dataset containing digitizer
        data. The dataset naming follows two formats based on their
        associated adc::

            # for 'SIS 3302'
            '<config_name> [Slot <slot>: SIS 3302 ch <ch>]'

            # for 'SIS 3305'
            '<config_name> [Slot <slot>: SIS 3305 FPGA <num> ch <ch>]'

        where `<config_name>` is the digitizer configuration name,
        `<slot>` is the slot number in the digitizer crate that is
        associated with the board number, `<ch>` is the requested
        channel number, and `<num>` is the FPGA number.  Only the
        'SIS 3305' utilizes the FPGA nomenclature, where channels 1-4
        reside on 'FPGA 1' and channels 5-8 reside on 'FPGA 2'.

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

        # Condition adc
        # - if adc is not specified then the slow adc '3302' is assumed
        #   or, if 3305 is the only active adc, then it is assumed
        # - self.__config_crates() always adds 'SIS 3302' first. If
        #   '3302' is not active then the list will only contain '3305'.
        if adc is None:
            if len(self.configs[config_name]["adc"]) == 1:
                adc = self.configs[config_name]["adc"][0]
                warn(
                    f"No `adc` specified, but only one adc used..."
                    f"assuming adc '{adc}'"
                )
            else:
                # there should never be a case where there are NO active
                # adc's, this covers the case where there is MULTIPLE
                # adc's
                #
                adc = "SIS 3302"
                warn("No `adc` specified...assuming adc 'SIS 3302'")
        elif adc not in self._configs[config_name]["adc"]:
            raise ValueError(
                f"Specified adc ({adc}) is not in specified configuration "
                f"({config_name})."
            )

        # search if (board, channel) combo is connected
        bc_valid = False
        d_info = None
        for brd, chs, extras in self._configs[config_name][adc]:
            if board == brd and channel in chs:
                # board, channel combo valid
                bc_valid = True

                # save adc settings for return if requested
                if return_info:
                    d_info = extras
                    d_info["adc"] = adc
                    d_info["configuration name"] = config_name
                    d_info["digitizer"] = self._info["group name"]
                break

        # (board, channel) combo must be active
        if bc_valid is False:
            raise ValueError(
                "Input `board` and `channel` do NOT specified a valid dataset."
            )

        # checks passed, build dataset_name
        slot = self.get_slot(board, adc)
        if adc == "SIS 3302":
            dataset_name = f"{config_name} [Slot {slot}: SIS 3302 ch {channel}]"
        else:
            # this is 'SIS 3305'
            if channel in range(1, 5):
                fpga = 1
                ch = channel
            else:
                fpga = 2
                ch = channel - 4

            dataset_name = f"{config_name} [Slot {slot}: SIS 3305 FPGA {fpga} ch {ch}]"

        # return
        if return_info is True:
            return dataset_name, d_info
        else:
            return dataset_name

    def construct_header_dataset_name(
        self, board: int, channel: int, config_name=None, adc=None, **kwargs
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

    def get_slot(self, brd: int, adc: str) -> Union[None, int]:
        """
        Get slot number for given board number and adc.

        :param brd: board number
        :param adc: digitizer analog-digital-converter name
        :returns: slot number, or :code:`None` if there is no associated
            slot number
        """
        slot = None
        for s, info in self.slot_info.items():
            if brd == info[0] and adc == info[1]:
                slot = s
                break

        return slot

    @property
    def slot_info(self) -> Dict[int, Tuple[int, str]]:
        """
        Slot info dictionary.  Contains relationship between slot
        number and the associated board number and adc name.
        """
        slot_info = {
            5: (1, "SIS 3302"),
            7: (2, "SIS 3302"),
            9: (3, "SIS 3302"),
            11: (4, "SIS 3302"),
            13: (1, "SIS 3305"),
            15: (2, "SIS 3305"),
        }
        return slot_info
