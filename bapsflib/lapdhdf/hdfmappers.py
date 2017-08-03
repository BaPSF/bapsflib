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
    known_hdf_version = {'1.1': hdfMap_LaPD_1dot1,
                         '1.2': hdfMap_LaPD_1dot2}
    if hdf_version in known_hdf_version.keys():
        class hdfMap(known_hdf_version[hdf_version]):
            def __init__(self):
                super(hdfMap, self).__init__()

        return hdfMap
    else:
        print('Mapping of HDF5 file is not known.\n')


class hdfMapTemplate(object):
    _msi_group = 'MSI'
    _msi_diagnostic_groups = []
    _data_group = 'Raw data + config'

    def __init__(self):
        pass


class hdfMap_LaPD_1dot1(hdfMapTemplate):
    def __init__(self):
        super(hdfMapTemplate, self).__init__()


class hdfMap_LaPD_1dot2(hdfMapTemplate):
    def __init__(self):
        super(hdfMap_LaPD_1dot2, self).__init__()
