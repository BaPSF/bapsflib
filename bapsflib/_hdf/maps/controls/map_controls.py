# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2019 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
"""Module for defining the main control mapper `HDFMapControls`."""

__all__ = ["HDFMapControls"]

import h5py

from typing import Dict, Tuple, Type

from bapsflib._hdf.maps.controls.bmotion import HDFMapControlBMotion
from bapsflib._hdf.maps.controls.n5700ps import HDFMapControlN5700PS
from bapsflib._hdf.maps.controls.nixyz import HDFMapControlNIXYZ
from bapsflib._hdf.maps.controls.nixz import HDFMapControlNIXZ
from bapsflib._hdf.maps.controls.phys180e import HDFMapControlPositions180E
from bapsflib._hdf.maps.controls.sixk import HDFMapControl6K
from bapsflib._hdf.maps.controls.templates import (
    ControlMap,
    HDFMapControlCLTemplate,
    HDFMapControlTemplate,
)
from bapsflib._hdf.maps.controls.waveform import HDFMapControlWaveform
from bapsflib.utils import TableDisplay
from bapsflib.utils.exceptions import HDFMappingError


class HDFMapControls(dict):
    """
    A dictionary that contains mapping objects for all the discovered
    control devices in the HDF5 data group.  The dictionary keys are
    the names of the discovered control devices.
    """

    _defined_mapping_classes = {
        "180E_positions": HDFMapControlPositions180E,
        "6K Compumotor": HDFMapControl6K,
        "bmotion": HDFMapControlBMotion,
        "N5700_PS": HDFMapControlN5700PS,
        "NI_XYZ": HDFMapControlNIXYZ,
        "NI_XZ": HDFMapControlNIXZ,
        "Waveform": HDFMapControlWaveform,
    }  # type: Dict[str, Type[HDFMapControlTemplate]]
    """
    Dictionary containing references to the defined (known) control
    device mapping classes.
    """

    def __init__(self, data_group: h5py.Group):
        """
        Parameters
        ----------
        data_group : `h5py.Group`
            HDF5 group object to be mapped

        Examples
        --------

            >>> from bapsflib import lapd
            >>> from bapsflib._hdf.maps import HDFMapControls
            >>> f = lapd.File('sample.hdf5')
            >>> # 'Raw data + config' is the LaPD HDF5 group name for the
            ... # group housing digitizer and control devices
            ... control_map = HDFMapControls(f['Raw data + config'])
            >>> control_map['6K Compumotor']
            <bapsflib._hdf.maps.controls.sixk.HDFMapControl6K>
        """
        # condition data_group arg
        if not isinstance(data_group, h5py.Group):
            raise TypeError("data_group is not of type h5py.Group")

        # store HDF5 data group
        self.__data_group = data_group

        # Gather data_group subgroups
        # - each of these subgroups can fall into one of four 'LaPD
        #   data types'
        #   1. data sequence
        #   2. digitizer groups (known)
        #   3. controls (known)
        #   4. unknown
        #
        self.data_group_subgnames = []
        for gname in data_group:
            if isinstance(data_group[gname], h5py.Group):
                self.data_group_subgnames.append(gname)

        # Build the self dictionary
        dict.__init__(self, self.__build_dict)

    def __str__(self):
        if len(self) == 0:
            # no controls mapped
            return ""

        # gather information
        rows = [
            [
                "Control",
                "Configuration",
                "Shot Num. Range",
                "Readout Data Fields",
            ],
        ]
        for control_name, _map in self.items():
            control_name_added = False
            for cname, config in _map.configs.items():
                control_entry = "" if control_name_added else f"'{control_name}'"
                rows.append(
                    [
                        control_entry,
                        f"'{cname}'",
                        "??",
                        str(tuple(config["state values"].keys())),
                    ]
                )

                control_name_added = True

        table_display = TableDisplay(rows=rows[1:], headers=rows[0])
        table_display.auto_insert_horizontal_dividers(on_columns=[0])
        table_str = table_display.table_string()

        return table_str

    def __repr__(self):
        _repr = super().__repr__()
        _repr += f"\n\n{self.__str__()}"
        return _repr

    @property
    def mappable_devices(self) -> Tuple[str, ...]:
        """
        tuple of the mappable control devices (i.e. their HDF5 group
        names)
        """
        return tuple(self._defined_mapping_classes.keys())

    @property
    def __build_dict(self) -> Dict[str, ControlMap]:
        """
        Discovers the HDF5 control devices and builds the dictionary
        containing the control device mapping objects.  This is the
        dictionary used to initialize ``self``.

        Returns
        -------
        dict
            control device mapping dictionary
        """
        control_dict = {}

        # update the mapping dictionary to include the original keys, as
        # well as the associated EXPECTED_GROUP_NAME
        _mapper_dict = (
            {}
        )  # type: Dict[str, Tuple[Tuple[str, Type[HDFMapControlTemplate]], ...]]
        for key, mapper in self._defined_mapping_classes.items():
            _mapper_dict[key] = ((key, mapper),)

            if mapper._EXPECTED_GROUP_NAME is None:
                continue

            alt_key = str(mapper._EXPECTED_GROUP_NAME)
            if alt_key not in _mapper_dict:
                _mapper_dict[alt_key] = ((key, mapper),)
            else:
                mappers = list(_mapper_dict.pop(alt_key))
                mappers.append((key, mapper))

                _mapper_dict[alt_key] = tuple(mappers)

        # try mapping
        for name in self.data_group_subgnames:
            try:
                _mappers = _mapper_dict[name]
            except KeyError:
                # group name `name` does not match any key of _defined_mapping_classes,
                # check `name` against the mapper EXPECTED_GROUP_NAME
                continue

            for _key, _mapper in _mappers:
                try:
                    # Note: always add to the control dictionary using
                    #       the original key, and not the alternate key
                    #       that corresponds to the _EXPECTED_GROUP_NAME
                    #       map class attribute
                    #
                    _map = _mapper(self.__data_group[name])
                    control_dict[_key] = _map
                except HDFMappingError:
                    # mapping failed
                    continue

        # return dictionary
        return control_dict
