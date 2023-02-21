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
import h5py
import numpy as np

from typing import Dict, Iterable, Tuple, Union
from warnings import warn


class FauxSISCrate(h5py.Group):
    """
    Creates a Faux 'SIS crate' Group in a HDF5 file.
    """

    # noinspection SpellCheckingInspection,PyProtectedMember
    class Knobs(object):
        """
        A class that contains all the controls for specifying the
        digitizer group structure.
        """

        def __init__(self, val):
            super().__init__()
            self._faux = val

        @property
        def active_brdch(self):
            """
            Boolean numpy array of active board, channel combinations.
            Shape = (13, 8) 13 boards and 8 channels
            """
            return self._faux._active_brdch.copy()

        @active_brdch.setter
        def active_brdch(self, val):
            """
            Set the active board, channel combinations
            """
            if not isinstance(val, np.ndarray):
                warn("`val` not valid, no update performed")
                return
            elif val.shape != ():
                warn("`val` not valid, no update performed")
                return
            elif not all(name in val.dtype.names for name in self._faux.device_adcs):
                warn("`val` not valid, no update performed")
                return
            elif val.dtype["SIS 3302"].shape != (4, 8) or val.dtype["SIS 3305"].shape != (
                2,
                8,
            ):
                warn("`val` not valid, no update performed")
                return
            elif not np.any(val["SIS 3302"]) and not np.any(val["SIS 3305"]):
                warn("`val` not valid, no update performed")
                return

            # check against 'SIS 3305' mode
            # - prevent enabling channels that can't be enabled for
            #   the SIS 3305 mode
            if self.sis3305_mode == 2:
                mask = np.array(2 * [True, False, False, False], dtype=bool)
            elif self.sis3305_mode == 1:
                mask = np.array(2 * [True, False, True, False], dtype=bool)
            else:
                mask = np.ones(8, dtype=bool)
            mask = np.logical_not(mask)
            mask = mask.reshape(1, 8)
            mask = np.append(mask, mask, axis=0)
            if np.any(val["SIS 3305"][mask]):
                warn("`val` not valid, no update performed")
                return

            # we're good
            self._faux._active_brdch = val
            self._faux._update()

        @property
        def active_config(self):
            """current active configuration"""
            return self._faux._active_config

        @active_config.setter
        def active_config(self, val):
            if not isinstance(val, Iterable) or isinstance(val, str):
                val = (val,)
            elif isinstance(val, tuple):
                pass
            else:
                val = tuple(val)

            # if val in self._faux._config_names:
            if all(cname in self._faux._config_names for cname in val):
                if val != self._faux._active_config:
                    self._faux._active_config = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        @property
        def n_configs(self):
            """Number of SIS 3301 configurations"""
            return self._faux._n_configs

        @n_configs.setter
        def n_configs(self, val):
            """Set number of waveform configurations"""
            if val >= 1 and isinstance(val, int):
                if val != self._faux._n_configs:
                    self._faux._n_configs = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        @property
        def nt(self):
            """Number of temporal samples"""
            return self._faux._nt

        @nt.setter
        def nt(self, val):
            """Set the number of temporal samples"""
            if isinstance(val, int):
                if val != self._faux._nt:
                    self._faux._nt = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        @property
        def sis3305_mode(self):
            """
            SIS 3305 acquisition mode. (0 = 1.25 GHz, 1 = 2.5 GHZ,
            2 = 5 GHz)
            """
            return self._faux._sis3305_mode

        @sis3305_mode.setter
        def sis3305_mode(self, val):
            """
            Set SIS 3305 acquisition mode. (0 = 1.25 GHz, 1 = 2.5 GHZ,
            2 = 5 GHz)
            """
            if val in (0, 1, 2):
                if val != self._faux._sis3305_mode:
                    self._faux._sis3305_mode = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        @property
        def sn_size(self):
            """Number of shot numbers in a dataset"""
            return self._faux._sn_size

        @sn_size.setter
        def sn_size(self, val):
            """Set the number of shot numbers in a dataset"""
            if isinstance(val, int) and val >= 1:
                if val != self._faux._sn_size:
                    self._faux._sn_size = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        def reset(self):
            """Reset 'SIS 3301' group to defaults."""
            self._faux._default_setup()
            self._faux._update()

    def __init__(self, id, n_configs=1, sn_size=100, nt=10000, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError(f"{id} is not a GroupID")

        # create control group
        # noinspection PyUnresolvedReferences
        gid = h5py.h5g.create(id, b"SIS crate")
        h5py.Group.__init__(self, gid)

        # define key values
        self._default_setup()
        if n_configs != self._n_configs:
            self._n_configs = n_configs
        if sn_size != self._sn_size:
            self._sn_size = sn_size
        if nt != self._nt:
            self._nt = nt

        # define slot info dict
        self._slot_info = {
            3: (-1, "SIS 3820", 939524096),
            5: (1, "SIS 3302", 1342177280),
            7: (2, "SIS 3302", 1476395008),
            9: (3, "SIS 3302", 1610612736),
            11: (4, "SIS 3302", 1744830464),
            13: (1, "SIS 3305", 2684354560),
            15: (2, "SIS 3305", 2701131776),
        }

        # set root attributes
        self._set_siscrate_attrs()

        # build control device sub-groups, datasets, and attributes
        self._update()

    def _build_config_group(self, config_name: str):
        """
        Creates and populates the digitizer configuration group.

        :param config_name: name of digitizer configuration
        """
        # TODO: consider adding calibration sub-groups
        # create configuration group
        gname = config_name
        self.create_group(gname)

        # -- set attributes for configuration group                 ----
        brd_slot_num = [
            3,
        ]
        brd_types = [
            4,
        ]
        brd_config_indices = [
            0,
        ]
        brd_address = [
            self.slot_info[brd_slot_num[0]][2],
        ]
        for field in ("SIS 3305", "SIS 3302"):
            config_index = 0
            brd_bool_arr = np.any(self._active_brdch[field], axis=1)
            brd_index = np.where(brd_bool_arr)[0]
            for brd in brd_index:
                # determine slot number
                slot = self.get_slot(brd + 1, field)
                if slot is None:
                    warn(f"Got no slot number for board number {brd+1}")
                    continue

                # update lists
                brd_slot_num.append(slot)
                brd_types.append(3 if field == "SIS 3305" else 2)
                brd_config_indices.append(config_index)
                brd_address.append(self.slot_info[slot][2])

                # increment config index
                config_index += 1

        # update attributes
        self[gname].attrs.update(
            {
                "SIS crate base addresses": np.array(brd_address, dtype=np.uint32),
                "SIS crate board types": np.array(brd_types, dtype=np.uint32),
                "SIS crate config indices": np.array(brd_config_indices, dtype=np.uint32),
                "SIS crate max average shots": np.int32(1),
                "SIS crate slot numbers": np.array(brd_slot_num, dtype=np.uint32),
            }
        )

        # -- Create and Populate Configuration Sub-Groups           ----
        for slot, index in zip(brd_slot_num, brd_config_indices):
            adc = self.slot_info[slot][1]
            if adc == "SIS 3820":
                self._build_config_sis3820_subgroup(config_name, slot, index)
            elif adc == "SIS 3302":
                self._build_config_sis3302_subgroup(config_name, slot, index)
            elif adc == "SIS 3305":
                self._build_config_sis3305_subgroup(config_name, slot, index)

    def _build_config_sis3302_subgroup(self, config_name: str, slot: int, index: int):
        """
        Create and set attributes for a SIS 3302 configuration group.
        """
        # create group
        gname = f"SIS crate 3302 configurations[{index}]"
        gpath = f"{config_name}/{gname}"
        self.create_group(gpath)

        # get channel array
        brd = self.slot_info[slot][0]
        sis_arr = self._active_brdch["SIS 3302"][brd - 1]

        # populate attributes
        self[gpath].attrs.update(
            {
                "Clock rate": np.uint32(7),
                "Sample averaging (hardware)": np.uint32(0),
                "Samples": np.uint32(self.knobs.nt),
                "Shot averaging (software)": np.int32(1),
            }
        )
        for ii in range(1, 9):
            # 'Ch #' fields
            field = f"Ch {ii}"
            self[gpath].attrs[field] = np.int32(ii)

            # 'Comment #' fields
            field = f"Comment {ii}"
            self[gpath].attrs[field] = np.bytes_("")

            # 'DC offset #' fields
            field = f"DC offset {ii}"
            self[gpath].attrs[field] = np.float64(0.0)

            # 'Data type #' fields
            field = f"Data type {ii}"
            self[gpath].attrs[field] = np.bytes_(f"probe name {ii}")

            # 'Enabled #' fields
            field = f"Enabled {ii}"
            self[gpath].attrs[field] = np.bytes_("TRUE" if sis_arr[ii - 1] else "FALSE")

    def _build_config_sis3305_subgroup(self, config_name: str, slot: int, index: int):
        """
        Create and set attributes for a SIS 3305 configuration group.
        """
        # create group
        gname = f"SIS crate 3305 configurations[{index}]"
        gpath = f"{config_name}/{gname}"
        self.create_group(gpath)

        # get channel array
        brd = self.slot_info[slot][0]
        sis_arr = self._active_brdch["SIS 3305"][brd - 1]

        # populate attributes
        self[gpath].attrs.update(
            {
                "Bandwidth": np.uint32(1),
                "Channel mode": np.uint32(self._sis3305_mode),
                "Clock rate": np.uint32(0),
                "Samples": np.uint32(self.knobs.nt),
                "Shot averaging (software)": np.int32(1),
            }
        )
        for ii in range(1, 9):
            # setup
            if 1 <= ii <= 4:
                fpga_str = "FPGA 1 "
                ch = ii
            else:
                fpga_str = "FPGA 2 "
                ch = ii - 4

            # 'FPGA # Avail #' fields
            if self._sis3305_mode == 2 and ch != 1:
                mode = "FALSE"
            elif self._sis3305_mode == 1 and ch not in (1, 3):
                mode = "FALSE"
            else:
                mode = "TRUE"
            field = f"{fpga_str}Avail {ch}"
            self[gpath].attrs[field] = np.bytes_(mode)

            # 'FPGA # Ch #' fields
            field = f"{fpga_str}Ch {ch}"
            self[gpath].attrs[field] = np.int32(ii)

            # 'FPGA # Comment #' fields
            field = f"{fpga_str}Comment {ch}"
            self[gpath].attrs[field] = np.bytes_("")

            # 'FPGA # Data type #' fields
            field = f"{fpga_str}Data type {ch}"
            self[gpath].attrs[field] = np.bytes_(f"probe name {ii}")

            # 'FPGA # Enabled #' fields
            field = f"{fpga_str}Enabled {ch}"
            self[gpath].attrs[field] = np.bytes_("TRUE" if sis_arr[ii - 1] else "FALSE")

    def _build_config_sis3820_subgroup(self, config_name: str, slot: int, index: int):
        """
        Create and set attributes for a SIS 3820 configuration group.
        """
        # create group
        gname = f"SIS crate 3820 configurations[{index}]"
        gpath = f"{config_name}/{gname}"
        self.create_group(gpath)

        # populate attributes
        self[gpath].attrs.update(
            {
                "Clock frequency divider": np.uint32(1),
                "Clock mode": np.uint32(1),
                "Clock source": np.uint32(1),
                "Delay": np.uint32(0),
                "Even outputs": np.uint32(1),
                "Odd outputs": np.uint32(0),
            }
        )

    def _build_datasets(self):
        """Create and populate all datasets."""
        self._build_datasets_sis3302()
        self._build_datasets_sis3305()

    def _build_datasets_sis3302(self):
        """Create and populate datasets related to SIS 3302."""
        bc_arr = np.where(self._active_brdch["SIS 3302"])

        for board, channel in zip(bc_arr[0], bc_arr[1]):
            brd = board + 1
            ch = channel + 1
            slot = self.get_slot(brd, "SIS 3302")

            for cname in self._active_config:
                # create main dataset
                dset_name = f"{cname} [Slot {slot}: SIS 3302 ch {ch}]"
                shape = (self._sn_size, self._nt)
                data = np.empty(shape=shape, dtype=np.int16)
                self.create_dataset(dset_name, data=data)

                # create header dataset
                hdset_name = f"{dset_name} headers"
                shape = (self._sn_size,)
                dtype = np.dtype(
                    [
                        ("Shot number", np.int32),
                        ("Scale", np.float32),
                        ("Offset", np.float32),
                        ("Min", np.uint16),
                        ("Max", np.uint16),
                        ("Clipped", np.int8),
                    ]
                )
                dheader = np.empty(shape=shape, dtype=dtype)
                dheader["Shot number"] = np.arange(
                    1, shape[0] + 1, 1, dtype=dheader["Shot number"].dtype
                )
                dheader["Scale"] = 7.7241166e-5
                dheader["Offset"] = -2.531
                dheader["Min"] = data.min(axis=1)
                dheader["Max"] = data.max(axis=1)
                dheader["Clipped"] = 0
                self.create_dataset(hdset_name, data=dheader)

    def _build_datasets_sis3305(self):
        """Create and populate datasets related to SIS 3305."""
        bc_arr = np.where(self._active_brdch["SIS 3305"])

        for board, channel in zip(bc_arr[0], bc_arr[1]):
            brd = board + 1
            ch = channel + 1
            slot = self.get_slot(brd, "SIS 3305")
            if 1 <= ch <= 4:
                fpga_str = "FPGA 1"
            else:
                fpga_str = "FPGA 2"
                ch = ch - 4

            for cname in self._active_config:
                # create main dataset
                dset_name = f"{cname} [Slot {slot}: SIS 3305 {fpga_str} ch {ch}]"
                shape = (self._sn_size, self._nt)
                data = np.empty(shape=shape, dtype=np.int16)
                self.create_dataset(dset_name, data=data)

                # create header dataset
                hdset_name = f"{dset_name} headers"
                shape = (self._sn_size,)
                dtype = np.dtype(
                    [
                        ("Shot number", np.int32),
                        ("Scale", np.float32),
                        ("Offset", np.float32),
                        ("Min", np.uint16),
                        ("Max", np.uint16),
                        ("Clipped", np.int8),
                    ]
                )
                dheader = np.empty(shape=shape, dtype=dtype)
                dheader["Shot number"] = np.arange(
                    1, shape[0] + 1, 1, dtype=dheader["Shot number"].dtype
                )
                dheader["Scale"] = 0.0019550342
                dheader["Offset"] = -1.0
                dheader["Min"] = data.min(axis=1)
                dheader["Max"] = data.max(axis=1)
                dheader["Clipped"] = 0
                self.create_dataset(hdset_name, data=dheader)

    def _default_setup(self):
        """Set group setup parameters to defaults"""
        self._n_configs = 1
        self._sn_size = 100
        self._nt = 10000
        self._active_brdch = np.zeros(
            (), dtype=[("SIS 3302", bool, (4, 8)), ("SIS 3305", bool, (2, 8))]
        )
        self._active_brdch["SIS 3302"][0][0] = True
        self._active_brdch["SIS 3305"][0][0] = True
        self._config_names = []
        self._active_config = ("config01",)
        self._sis3305_mode = 0

    def _set_siscrate_attrs(self):
        """Sets the 'SIS crate' group attributes"""
        self.attrs.update(
            {
                "Created date": np.bytes_("8/21/2012 12:26:06 PM"),
                "Description": np.bytes_(
                    "SIS Crate of Digitizers:\n\n"
                    "4 type 3302 boards: 8 channels per board, 100MHz per "
                    "channel, 16 bit vertical resolution, "
                    "1MSamp/channel\n\n"
                    "2 type 3305 boards: 8 channels per board, 1.25GHz "
                    "per channel, 10 bit vertical resolution. 2GB memory "
                    "per board.\n\n"
                    "Each 3305 board can be switched to be 4 channels at "
                    "2.5 GHz, or 2 channels at 5.0GHz.\n"
                    "This module also provides access to the clock "
                    "distributor board."
                ),
                "Device name": np.bytes_("SIS crate"),
                "Module IP address": np.bytes_("192.168.7.3"),
                "Module VI path": np.bytes_("Modules\SIS crate\SIS crate.vi"),
                "Type": np.bytes_("Data acquisition"),
            }
        )

    def _update(self):
        """
        Updates digitizer group structure (Groups, Datasets, and
        Attributes)
        """
        # clear group before rebuild
        self.clear()

        # build configuration groups
        self._config_names = []
        for i in range(self._n_configs):
            config_name = f"config{i+1:02}"
            self._config_names.append(config_name)
            self._build_config_group(config_name)

        # reset active configuration if necessary
        if not all(cname in self._config_names for cname in self._active_config):
            self._active_config = (self._config_names[0],)

        # build datasets
        self._build_datasets()

    @property
    def config_names(self):
        """list of 'SIS 3301' configuration names"""
        return self._config_names.copy()

    @property
    def device_adcs(self):
        """List of adc's integrated into the digitizer."""
        return ["SIS 3302", "SIS 3305"]

    def get_slot(self, board: int, adc: str) -> Union[int, None]:
        """Get slot number for given board number and adc."""
        slot = None
        for s, info in self.slot_info.items():
            if board == info[0] and adc == info[1]:
                slot = s
                break

        return slot

    @property
    def knobs(self):
        """Knobs for controlling structure of digitizer group"""
        return self.Knobs(self)

    @property
    def slot_info(self) -> Dict[int, Tuple[int, str, int]]:
        """
        Slot number info dictionary.
        """
        return self._slot_info
