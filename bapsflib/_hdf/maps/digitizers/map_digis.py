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
"""Module for defining the main digitizer mapper `HDFMapDigitizers`."""
__all__ = ["HDFMapDigitizers"]

import h5py

from typing import Dict, Tuple

from bapsflib._hdf.maps.digitizers.sis3301 import HDFMapDigiSIS3301
from bapsflib._hdf.maps.digitizers.siscrate import HDFMapDigiSISCrate
from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate
from bapsflib.utils.exceptions import HDFMappingError


class HDFMapDigitizers(dict):
    """
    A dictionary that contains mapping objects for all the discovered
    digitizers in the HDF5 data group.  The dictionary keys are the
    names of he discovered digitizers.

    :Example:

        >>> from bapsflib import lapd
        >>> from bapsflib._hdf.maps import HDFMapDigitizers
        >>> f = lapd.File('sample.hdf5')
        >>> # 'Raw data + config' is the LaPD HDF5 group name for the
        ... # group housing digitizer and control devices
        ... digi_map = HDFMapDigitizers(f['Raw data + config'])
        >>> digi_map['SIS 3301']
        <bapsflib._hdf.maps.digitizers.sis3301.HDFMapDigiSIS3301>
    """

    _defined_mapping_classes = {
        "SIS 3301": HDFMapDigiSIS3301,
        "SIS crate": HDFMapDigiSISCrate,
    }
    """
    Dictionary containing references to the defined (known) digitizer 
    mapping classes.
    """

    def __init__(self, data_group: h5py.Group):
        """
        :param data_group: HDF5 group object
        """
        # condition data_group arg
        if not isinstance(data_group, h5py.Group):
            raise TypeError("data_group is not of type h5py.Group")

        # store HDF5 data group instance
        self.__data_group = data_group

        # Build the self dictionary
        dict.__init__(self, self.__build_dict)

    @property
    def mappable_devices(self) -> Tuple[str, ...]:
        """
        Tuple of the mappable digitizers (i.e. their HDF5 group names)
        """
        return tuple(self._defined_mapping_classes)

    @property
    def __build_dict(self) -> Dict[str, HDFMapDigiTemplate]:
        """
        Discovers the HDF5 digitizers and builds the dictionary
        containing the digitizer mapping objects.  This is the
        dictionary used to initialize :code:`self`.

        :return: digitizer mapping dictionary
        :rtype: dict
        """
        # all data_group subgroups
        # - each of these subgroups can fall into one of four 'LaPD
        #   data types'
        #   1. data sequence
        #   2. digitizer groups (known)
        #   3. controls (known)
        #   4. unknown
        #
        #: list of all group names in the HDF5 data group
        subgnames = []
        for name in self.__data_group:
            if isinstance(self.__data_group[name], h5py.Group):
                subgnames.append(name)

        # build dictionary
        digi_dict = {}
        for name in subgnames:
            if name in self._defined_mapping_classes:
                # only add mappings that succeed
                try:
                    digi_dict[name] = self._defined_mapping_classes[name](
                        self.__data_group[name]
                    )
                except HDFMappingError:
                    # mapping failed
                    pass

        # return dictionary
        return digi_dict
