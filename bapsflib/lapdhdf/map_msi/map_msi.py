# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2018 Erik T. Everson and contributors
#
# License:
#
# TODO: determine a default structure for all diagnostic msi classes
#
import h5py

from .interferometerarray import hdfMap_msi_interarr


class hdfMap_msi(dict):
    """
    A dictionary that contains mapping objects for all the discovered
    MSI diagnostics in the HDF5 MSI group.  The dictionary keys are the
    discovered MSI diagnostic names.
    """
    _defined_diagnostic_mappings = {
        'Interferometer array': hdfMap_msi_interarr,
    }
    """
    Dictionary containing references to the defined (known) MSI
    diagnostic mapping classes.
    """
    # __defined_diagnostic_mappings = {
    #     'Discharge': 'discharge map',
    #     'Gas pressure': 'gas pressure map',
    #     'Heater': 'heater map',
    #     'Interferometer array': 'inter map',
    #     'Magnetic field': 'magnetic field map'}

    def __init__(self, msi_group):

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
        :return: list of the pre-defined MSI diagnostic group names
        :rtype: list(str)
        """
        return list(self._defined_diagnostic_mappings.keys())

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
        try:
            for name in self.msi_group_subgnames:
                if name in self._defined_diagnostic_mappings:
                    # only add mapping that succeeded
                    diag_map = \
                        self._defined_diagnostic_mappings[name](
                            self.__msi_group[name])
                    if diag_map.build_successful:
                        msi_dict[name] = diag_map

        except TypeError:
            pass

        # return dictionary
        return msi_dict
