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


class hdfMap_msi(dict):
    __defined_diagnostic_mappings = {
        'Discharge': 'discharge map',
        'Gas pressure': 'gas pressure map',
        'Heater': 'heater map',
        'Interferometer array': 'inter map',
        'Magnetic field': 'magnetic field map'}

    def __init__(self, msi_group):

        # condition msi_group arg
        if not isinstance(msi_group, h5py.Group):
            raise TypeError('msi_group is not of type h5py.Group')

        self.__msi_group = msi_group

        # Determine Diagnostics in msi
        # - it is assumed that any subgroup of 'MSI/' is a diagnostic
        # - any dataset directly under 'MSI/' is ignored
        self.found_diagnostics = []
        for key in msi_group.keys():
            if isinstance(msi_group[key], h5py.Group):
                self.found_diagnostics.append(key)

        if len(self.found_diagnostics) == 0:
            self.found_diagnostics = None

        # Build the self dictionary
        dict.__init__(self, self.__build_dict)

    @property
    def group(self):
        return self.__msi_group

    @property
    def predefined_diagnostic_groups(self):
        return list(self.__defined_diagnostic_mappings.keys())

    def is_diagnostic_in_context(self, diag_name):
        return diag_name in self.predefined_diagnostic_groups

    @property
    def __build_dict(self):
        # do not attach item if mapping is not known
        msi_dict = {}
        try:
            for item in self.found_diagnostics:
                if item in self.__defined_diagnostic_mappings.keys():
                    msi_dict[item] = \
                        self.__defined_diagnostic_mappings[item]
        except TypeError:
            pass

        return msi_dict
