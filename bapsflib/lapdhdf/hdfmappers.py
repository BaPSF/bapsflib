# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License:
#
# TODO: make a pickle save for the hdfMap...
#       Then, if a user adds additional mappings for a specific HDF5
#       file, those can be maintained
#
#
# Some hierarchical nomenclature for the digital acquisition system
#     DAQ       -- refers to the whole system, all digitizers, the
#                  computer system, etc.
#     digitizer -- a device that collects data, e.g. the main digitizer
#                  in the LaPD room, an oscilloscope, etc.
#     adc       -- analog-digital converter, the element of a digitizer
#                  that does the analog-to-digital conversion, e.g.
#                  the SIS 3302, SIS 3305, etc.
#     board     -- refers to a cluster of channels on an adc
#     channel   -- the actual hook-up location on the adc
#
import h5py
from .map_msi import hdfMap_msi
from .map_digitizers import hdfMap_digitizers


class hdfMap(object):
    """
    Template for all HDF Mapping Classes

    Class Attributes:
        msi_group  -- str -- name of MSI group
        data_group -- str -- name of data group

    Object Attributes:
        hdf_version  -- str
            - string representation of the version number
              corresponding the the LaPD HDF Software version used
              to generate the HDF5 file
        msi_diagnostic_groups -- [str]
            - list of the group names for each diagnostic recorded
              in the MSI group
        sis_group -- str
            - SIS group name which contains all the DAQ recorded
              data and associated DAQ configuration
        sis_crates -- [str]
            - list of SIS crates (digitizers) available to record
              data
        data_configs -- {}
            - dict containing key parameters associated with the
              crate configurations
            - dict is constructed using method build_data_configs

    Methods:
        sis_path
            - returns the HDF internal absolution path to the
              sis_group
        build_data_configs
            - used to construct the data_configs attribute
        parse_config_name
        is_config_active
        __config_crates
        __crate_info
        __find_crate_connections

    """
    # MSI stuff
    msi_group = 'MSI'

    # Data and Config stuff
    data_group = 'Raw data + config'

    # possible_digitizer_groups = {'main': ['SIS 3301', 'SIS crates'],
    #                             'aux': ['LeCroy', 'Waveform']}
    # possible_motion_groups = ['6K Compumotor', 'NI_XZ']
    # possible_dsequence_groups = ['Data run sequence']

    def __init__(self, hdf_obj):
        self.__hdf_obj = hdf_obj
        self.__attach_msi()
        self.__attach_digitizers()

    @property
    def has_msi_group(self):
        """
        :return: True/False if 'MSI/' group is detected
        """
        detected_msi = True if self.msi_group in self.__hdf_obj \
            else False
        return detected_msi

    @property
    def has_data_group(self):
        """
        :return: True/False if 'Raw data + config/' group is detected
        """
        detected_data = True if self.data_group in self.__hdf_obj \
            else False
        return detected_data

    @property
    def has_data_run_sequence(self):
        """
        :return: True/False if the 'Data run sequence/' group is found
            in the data group
        """
        return False

    @property
    def has_digitizers(self):
        """
        :return: True/False if any known digitizers are discovered in
            the data group
        """
        if not hasattr(self, 'digitizers'):
            has_digis = False
        elif self.digitizers is None:
            has_digis = False
        elif len(self.digitizers) == 0:
            has_digis = False
        else:
            has_digis = True
        return has_digis

    @property
    def has_motion_lists(self):
        """
        :return: True/False if any known motion groups are discovered in
            the data group
        """
        return False

    @property
    def has_unknown_data_subgoups(self):
        """
        :return: True/False if any unknown groups are discovered in the
            data groups. These groups could end up being digitizer
            groups and/or motion groups.
        """
        return False

    def __attach_msi(self):
        """
        Will attach a dictionary style mapper (self.msi) that contains
        all msi diagnostic mappings.

        :return:
        """
        if self.has_msi_group:
            self.msi = hdfMap_msi(self.__hdf_obj[self.msi_group])
        else:
            self.msi = None

    def __attach_digitizers(self):
        """
        Will attach a dictionary style mapper (self.digitizers) that
        contains all digitizer mappings.

        :return:
        """
        if self.has_data_group:
            self.digitizers = hdfMap_digitizers(
                self.__hdf_obj[self.data_group])
        else:
            self.digitizers = None

    @property
    def is_lapd_hdf(self):
        """
        :return: True/False if HDF5 file was generated by the LaPD
        """
        is_lapd = False
        for key in self.__hdf_obj.attrs.keys():
            if 'lapd' in key.casefold():
                is_lapd = True
                break

        return is_lapd

    @property
    def hdf_version(self):
        """
        :return: `str` identifying the LaPD DAQ Software version number
            used to generated the HDF5 file ('' if NOT LaPD generated)
        """
        vers = ''
        for key in self.__hdf_obj.attrs.keys():
            if 'version' in key.casefold():
                vers = self.__hdf_obj.attrs[key].decode('utf-8')
                break

        return vers

    @property
    def main_digitizer(self):
        """
        :return: an instance of the main digitizer in self.digitizers
        """
        possible_candidates = ['SIS 3301', 'SIS crate']
        digi = None
        for key in self.digitizers.keys():
            if key in possible_candidates:
                digi = self.digitizers[key]
                break

        return digi
