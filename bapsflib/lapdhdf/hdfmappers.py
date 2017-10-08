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
from .map_controls import hdfMap_controls


class hdfMap(object):
    """
    Constructs a complete file mapping of :py:obj:`hdf_obj` that is
    utilized by :py:class:`lapdhdf.File` to manipulate and read data out
    of the HDF5 file.

    :param hdf_obj: an object instance of :py:class:`lapdhdf.File`
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
        self.__attach_controls()

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
        elif self.__digitizers is None:
            has_digis = False
        elif len(self.__digitizers) == 0:
            has_digis = False
        else:
            has_digis = True
        return has_digis

    @property
    def has_controls(self):
        """
        :return: :code:`True`/:code:`False` if any known control groups
            are discovered in the data group
        """
        if not hasattr(self, 'controls'):
            has_controls = False
        elif self.controls is None:
            has_controls = False
        elif len(self.controls) == 0:
            has_controls = False
        else:
            has_controls = True
        return has_controls

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
        Will attach a dictionary style mapper (self.__msi) that contains
        all msi diagnostic mappings.
        """
        if self.has_msi_group:
            self.__msi = hdfMap_msi(self.__hdf_obj[self.msi_group])
        else:
            self.__msi = None

    @property
    def msi(self):
        """
        :return: A dictionary style container for all MSI diagnostic
            mappings.

        For example, to retrieve mappings of LaPD's Magnetic field one
        would call

        .. code-block:: python

            fmap = hdfMap(file_obj)
            bmap = fmap.msi['Magnetic field']
        """
        return self.__msi

    def __attach_digitizers(self):
        """
        Will attach a dictionary style mapper (self.__digitizers) that
        contains all digitizer mappings.
        """
        if self.has_data_group:
            self.__digitizers = hdfMap_digitizers(
                self.__hdf_obj[self.data_group])
        else:
            self.__digitizers = None

    @property
    def digitizers(self):
        """
        :return: A dictionary style container for all digitizer
            mappings.

        For example, to retrieve mappings of digitizer group 'SIS 3301'
        one would call

        .. code-block:: python

            fmap = hdfMap(file_obj)
            dmap = fmap.digitizers['SIS 3301']
        """
        return self.__digitizers

    def __attach_controls(self):
        """
        Will attach a dictionary style mapper (self.__controls) that
        contains all control mappings.
        """
        if self.has_data_group:
            self.__controls = hdfMap_controls(
                self.__hdf_obj[self.data_group])
        else:
            self.__controls = None

    @property
    def controls(self):
        """
        :return: A dictionary style container for all control mappings.

        For example, to retrieve mappings of the control group
        '6K Compumotor' one would call

        .. code-block:: python

            fmap = hdfMap(file_obj)
            mmap = fmap.controls['6K Compumotor']
        """
        return self.__controls

    def __attach_unknowns(self):
        """
        Will attach a dictionary style mapper (self.__unknowns) that
        contains all additional subgroups in :py:const:`data_group` that
        are unknown to the mapping constructor.
        """
        self.__unknowns = None

    @property
    def unknowns(self):
        """
        :return: A dictionary container for all subgroups in
            :py:const:`data_group` that are unknown to the mapping
            constructor.
        """
        return self.__unknowns

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

        The main digitizer is determine by scanning through the local
        tuple :py:const:`possible_candidates` that contains a
        hierarchical list of digitizers. The first digitizer found is
        considered the main digitizer.

        .. code-block:: python

            possible_candidates = ('SIS 3301', 'SIS crate')
        """
        # possible_candidates is a hierarchical tuple of all digitizers
        # such that the first found digitizer is assumed to be the main
        # digitizer
        possible_candidates = ('SIS 3301', 'SIS crate')
        digi = None
        if self.__digitizers is not None:
            for key in possible_candidates:
                if key in self.__digitizers:
                    digi = self.__digitizers[key]
                    break

        return digi
