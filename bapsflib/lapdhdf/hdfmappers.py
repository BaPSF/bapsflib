# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License:
#


def get_hdfMap(hdf_version):
    """
        Function to simulate a Class with dynamic inheritance.  An
        instance of the hdfMap class is returned.  The superclass
        inheritance of hdfMap is determined by the param hdf_version.

        :param hdf_version:
        :return:
    """
    known_hdf_version = {'1.1': hdfMap_LaPD_1dot1,
                         '1.2': hdfMap_LaPD_1dot2}

    if hdf_version in known_hdf_version.keys():
        class hdfMap(known_hdf_version[hdf_version]):
            """
                Contains the mapping relations for a given LaPD
                generated HDF5 file.
            """
            def __init__(self):
                super(hdfMap, self).__init__()

        hdf_mapping = hdfMap()
        return hdf_mapping
    else:
        print('Mapping of HDF5 file is not known.\n')


class hdfMapTemplate(object):
    hdf_version = ''
    msi_group = 'MSI'
    msi_diagnostic_groups = []
    data_group = 'Raw data + config'
    sis_group = ''
    sis_crates = []

    def __init__(self):
        pass

    def sis_path(self):
        return self.data_group + '/' + self.sis_group


class hdfMap_LaPD_1dot1(hdfMapTemplate):
    def __init__(self):
        hdfMapTemplate.__init__(self)

        self.hdf_version = '1.1'
        self.msi_diagnostic_groups.extend(['Discharge',
                                           'Gas pressure',
                                           'Heater',
                                           'Interferometer array',
                                           'Magnetic field'])
        self.sis_group = 'SIS 3301'
        self.sis_crates.append('SIS 3301')


class hdfMap_LaPD_1dot2(hdfMapTemplate):
    def __init__(self):
        hdfMapTemplate.__init__(self)

        self.hdf_version = '1.2'
        self.msi_diagnostic_groups.extend(['Discharge',
                                           'Gas pressure',
                                           'Heater',
                                           'Interferometer array',
                                           'Magnetic field'])
        self.sis_group = 'SIS crate'
        self.sis_crates.extend(['SIS 3302', 'SIS 3305'])
