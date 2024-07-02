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

from typing import Dict, Tuple, Union

from bapsflib._hdf.maps.controls.n5700ps import HDFMapControlN5700PS
from bapsflib._hdf.maps.controls.nixyz import HDFMapControlNIXYZ
from bapsflib._hdf.maps.controls.nixz import HDFMapControlNIXZ
from bapsflib._hdf.maps.controls.sixk import HDFMapControl6K
from bapsflib._hdf.maps.controls.templates import (
    HDFMapControlCLTemplate,
    HDFMapControlTemplate,
)
from bapsflib._hdf.maps.controls.waveform import HDFMapControlWaveform
from bapsflib.utils.exceptions import HDFMappingError

# define type aliases
ControlMap = Union[HDFMapControlTemplate, HDFMapControlCLTemplate]


class HDFMapControls(dict):
    """
    A dictionary that contains mapping objects for all the discovered
    control devices in the HDF5 data group.  The dictionary keys are
    the names of the discovered control devices.

    :Example:

        >>> from bapsflib import lapd
        >>> from bapsflib._hdf.maps import HDFMapControls
        >>> f = lapd.File('sample.hdf5')
        >>> # 'Raw data + config' is the LaPD HDF5 group name for the
        ... # group housing digitizer and control devices
        ... control_map = HDFMapControls(f['Raw data + config'])
        >>> control_map['6K Compumotor']
        <bapsflib._hdf.maps.controls.sixk.HDFMapControl6K>
    """

    _defined_mapping_classes = {
        "N5700_PS": HDFMapControlN5700PS,
        "NI_XYZ": HDFMapControlNIXYZ,
        "NI_XZ": HDFMapControlNIXZ,
        "6K Compumotor": HDFMapControl6K,
        "Waveform": HDFMapControlWaveform,
    }
    """
    Dictionary containing references to the defined (known) control
    device mapping classes.
    """

    def __init__(self, data_group: h5py.Group):
        """
        :param data_group: HDF5 group object
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
        dictionary used to initialize :code:`self`.

        :return: control device mapping dictionary
        :rtype: dict
        """
        control_dict = {}
        for name in self.data_group_subgnames:
            if name in self._defined_mapping_classes:
                # only add mapping that succeeded
                try:
                    _map = self._defined_mapping_classes[name](self.__data_group[name])
                    control_dict[name] = _map
                except HDFMappingError:
                    # mapping failed
                    pass

        # return dictionary
        return control_dict
