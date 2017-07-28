# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License:
#

import h5py

from .hdferrors import *


class hdfCheck(object):
    _msi_group = 'MSI'
    _msi_diagnostic_groups = ['Discharge', 'Gas pressure', 'Heater',
                              'Interferometer array', 'Magnetic field']
    _data_group = 'Raw data + config'
    _print_tab_len = 35

    def __init__(self, hdf_obj):
        if isinstance(hdf_obj, h5py.File):
            self._hdf_obj = hdf_obj
        else:
            raise NotHDFFileError

        self.check_msi()

    def check_msi(self):
        msi_detected = False
        for key in self._hdf_obj.keys():
            if key.casefold() == self._msi_group.casefold():
                msi_detected = True

        str_msi = self._msi_group + '/ '
        if msi_detected:
            str_msi += ' yes'.rjust(self._print_tab_len - 1
                                   - str_msi.__len__(), '~')
            print(str_msi)

            self.check_msi_diagnostics()
        else:
            str_msi += 'no'.rjust(self._print_tab_len - 1
                                  - str_msi.__len__(), '~')
            print(str_msi)

            raise NoMSIError

    def check_msi_diagnostics(self):
        for diag in self._msi_diagnostic_groups:
            diag_detected = False

            for key in self._hdf_obj[self._msi_group].keys():
                if key.casefold() == diag.casefold():
                    diag_detected = True

            str_diag = '|-- ' + diag + ' '
            if diag_detected:
                str_diag += ' yes'.rjust(self._print_tab_len - 1
                                         - str_diag.__len__(), '~')
            else:
                str_diag += ' no'.rjust(self._print_tab_len - 1
                                        - str_diag.__len__(), '~')

            print(str_diag)
