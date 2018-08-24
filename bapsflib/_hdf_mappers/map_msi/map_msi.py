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

from .discharge import hdfMap_msi_discharge
from .gaspressure import hdfMap_msi_gaspressure
from .heater import hdfMap_msi_heater
from .interferometerarray import hdfMap_msi_interarr
from .magneticfield import hdfMap_msi_magneticfield


class hdfMap_msi(dict):
    """
    A dictionary containing mapping objects for all the discovered
    MSI diagnostic HDF5 groups.  The dictionary keys are the MSI
    diagnostic names.

    :Example:

        >>> from bapsflib import lapd
        >>> from bapsflib._hdf_mappers import hdfMap_msi
        >>> f = lapd.File('sample.hdf5')
        >>> # 'MSI' is the LaPD HDF5 group name for the group housing
        ... # MSI diagnostic groups
        ... msi_map = hdfMap_msi(f['MSI'])
    """
    _defined_mapping_classes = {
        'Discharge': hdfMap_msi_discharge,
        'Gas pressure': hdfMap_msi_gaspressure,
        'Heater': hdfMap_msi_heater,
        'Interferometer array': hdfMap_msi_interarr,
        'Magnetic field': hdfMap_msi_magneticfield
    }
    """
    Dictionary containing references to the defined (known) MSI
    diagnostic mapping classes.
    """

    def __init__(self, msi_group: h5py.Group):
        """
        :param msi_group: HDF5 group object
        """
        # condition msi_group arg
        if not isinstance(msi_group, h5py.Group):
            raise TypeError('msi_group is not of type h5py.Group')

        # store HDF5 MSI group
        self.__msi_group = msi_group

        # Determine Diagnostics in msi
        # - it is assumed that any subgroup of 'MSI/' is a diagnostic
        # - any dataset directly under 'MSI/' is ignored
        self.msi_group_subgnames = []
        for diag in msi_group:
            if isinstance(msi_group[diag], h5py.Group):
                self.msi_group_subgnames.append(diag)

        # Build the self dictionary
        dict.__init__(self, self.__build_dict)

    @property
    def predefined_diagnostic_groups(self):
        """
        tuple of the mappable MSI diagnostics (i.e. their HDF5 group
        names)
        """
        return tuple(self._defined_mapping_classes.keys())

    @property
    def __build_dict(self):
        """
        Discovers the HDF5 MSI diagnostics and builds the dictionary
        containing the diagnostic mapping objects.  This is the
        dictionary used to initialize :code:`self`.

        :return: MSI diagnostic mapping dictionary
        :rtype: dict
        """
        # do not attach item if mapping is not known
        msi_dict = {}
        for name in self.msi_group_subgnames:
            if name in self._defined_mapping_classes:
                # only add mapping that succeeded
                diag_map = \
                    self._defined_mapping_classes[name](
                        self.__msi_group[name])
                if diag_map.build_successful:
                    msi_dict[name] = diag_map

        # return dictionary
        return msi_dict
