# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2018 Erik T. Everson and contributors
#
# License:
#


class Error(Exception):
    """
    Base class for exceptions in the lapdhdf module.
    """
    pass


class NotHDFFileError(Error):
    """
    Exception raised if desired object is not an instance of h5py.File.
    """

    def __init__(self):
        print('Object is not an instance of h5py.File.')


class NotLaPDHDFError(Error):
    """
    Exception raised if HDF5 file was not generated by the LaPD DAQ
    system.
    """
    def __init__(self):
        super().__init__('HDF5 File was not generated by LaPD System.')


class NotKnownLaPDHDFError(Error):
    """
    Exception raised if the HDF5 file was generated by the DAQ system
    but is not a known software version.
    """
    def __init__(self):
        print('HDF5 File was not generated by a known LaPD DAQ\n'
              + 'software version.')


class NoMSIError(Error):
    """
    Exception raised if no MSI group is detected in the opened HDF5
    file.
    """
    def __init__(self):
        print("No 'MSI/' detected in file.")