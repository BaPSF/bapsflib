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
    Constructs a complete file mapping of :obj:`hdf_obj` that is
    utilized by :class:`bapsflib.lapdhdf.files.File` to manipulate and
    read data out of the HDF5 file.

    The following classes are leveraged to construct the mappings:

    * :class:`~.map_controls.map_controls.hdfMap_controls`.
    * :class:`~.map_digitizers.map_digis.hdfMap_digitizers`.
    * :class:`~.map_msi.map_msi.hdfMap_msi`.
    """
    # MSI stuff
    msi_gname = 'MSI'
    """Name of the MSI HDF5 group."""

    # Data and Config stuff
    data_gname = 'Raw data + config'
    """Name of the DATA HDF5 group"""

    def __init__(self, hdf_obj):
        """
        :param hdf_obj: the HDF5 file object
        :type hdf_obj: :class:`h5py.File`
        """
        # store an instance of the HDF5 object for hdfMap
        self.__hdf_obj = hdf_obj

        # attach the mapping dictionaries
        self.__attach_msi()
        self.__attach_digitizers()
        self.__attach_controls()
        self.__attach_unknowns()

    @property
    def has_msi_group(self):
        """
        :return: :code:`True` if MSI group (:attr:`msi_gname`) is
            detected
        :rtype: bool
        """
        detected_msi = True if self.msi_gname in self.__hdf_obj \
            else False
        return detected_msi

    @property
    def has_data_group(self):
        """
        :return: :code:`True` if data group (:attr:`data_gname`) group
            is detected
        :rtype: bool
        """
        detected_data = True if self.data_gname in self.__hdf_obj \
            else False
        return detected_data

    @property
    def has_data_run_sequence(self):
        """
        :return: :code:`True` if the 'Data run sequence/' group is found
            in the data group
        :rtype: bool
        """
        # TODO: update when 'Data run squence/' is incorporated
        return False

    @property
    def has_diagnostics(self):
        """
        :return: :code:`True` if any known MSI diagnostics are
            discovered in the MSI group (i.e. :attr:`msi` is not empty)
        :rtype: bool
        """
        if not hasattr(self, 'msi'):
            has_diagnostics = False
        elif len(self.msi) == 0:
            has_diagnostics = False
        else:
            has_diagnostics = True
        return has_diagnostics

    @property
    def has_digitizers(self):
        """
        :return: :code:`True` if any known digitizers are discovered in
            the data group (i.e :attr:`digitizers` is not empty)
        :rtype: bool
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
        :return: :code:`True` if known control devices are discovered
            in the data group (i.e. :attr:`controls` is not empty)
        :rtype: bool
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
        :return: :code:`True` if there are any subgroups in the data
            group that are not known by the mapping constructors.
        """
        # TODO: need to implement
        return False

    def __attach_msi(self):
        """
        Attaches a dictionary (:attr:`__msi`) containing all MSI
        diagnostic mapping objects constructed by
        :class:`~.map_msi.map_msi.hdfMap_msi`.
        """
        if self.has_msi_group:
            self.__msi = hdfMap_msi(self.__hdf_obj[self.msi_gname])
        else:
            self.__msi = {}

    @property
    def msi(self):
        """
        :return: A dictionary containing all MSI diagnostic mappings
            objects.
        :rtype: dict

        For example, to retrieve mappings of LaPD's Magnetic field one
        would call::

            fmap = hdfMap(file_obj)
            bmap = fmap.msi['Magnetic field']
        """
        return self.__msi

    def __attach_digitizers(self):
        """
        Attaches a dictionary (:attr:`__digitizers`) containing all
        digitizer mapping objects constructed by
        :class:`~.map_digitizers.map_digis.hdfMap_digitizers`.
        """
        if self.has_data_group:
            self.__digitizers = hdfMap_digitizers(
                self.__hdf_obj[self.data_gname])
        else:
            self.__digitizers = {}

    @property
    def digitizers(self):
        """
        :return: A dictionary containing all digitizer mapping objects.
        :rtype: dict

        For example, to retrieve mappings of digitizer
        :code:`'SIS 3301'` one would call::

            fmap = hdfMap(file_obj)
            dmap = fmap.digitizers['SIS 3301']
        """
        return self.__digitizers

    def __attach_controls(self):
        """
        Attaches a dictionary (:attr:`__controls`) containing all
        control device mapping objects constructed by
        :class:`~.map_controls.map_controls.hdfMap_controls`.
        """
        if self.has_data_group:
            self.__controls = hdfMap_controls(
                self.__hdf_obj[self.data_gname])
        else:
            self.__controls = {}

    @property
    def controls(self):
        """
        :return: A dictionary containing all control device mapping
            objects.
        :rtype: dict

        For example, to retrieve mappings of the control device
        :code:`'6K Compumotor'` one would call::

            fmap = hdfMap(file_obj)
            mmap = fmap.controls['6K Compumotor']
        """
        return self.__controls

    def __attach_unknowns(self):
        """
        Attaches a list (:attr:`__unknowns`) with the subgroup names of
        all the subgroups in the data group (:attr:`data_gname`) that
        are unknown to the mapping constructors.
        """
        # TODO: need to implement
        self.__unknowns = {}

    @property
    def unknowns(self):
        """
        :return: A list containing all the subgroup names for the
            subgroups in the data group (:attr:`data_gname` that are
            unknown to the mapping constructor.
        :rtype: list
        """
        # TODO: need to implement
        return self.__unknowns

    @property
    def is_lapd_hdf(self):
        """
        :return: :code:`True` if the HDF5 file was generated by the LaPD
        :rtype: bool
        """
        is_lapd = False
        for key in self.__hdf_obj.attrs:
            if 'lapd' in key.casefold():
                is_lapd = True
                break

        return is_lapd

    @property
    def hdf_version(self):
        """
        :return: the LaPD DAQ Software version number used to generated
            the HDF5 file ('' if NOT LaPD generated)
        :rtype: str
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
        :return: the mapping object for the digitizer that is assumed
            to be the 'main digitizer' in :attr:`digitizers`

        The main digitizer is determine by scanning through the local
        tuple :const:`possible_candidates` that contains a
        hierarchical list of digitizers. The first digitizer found is
        assumed to be the 'main digitizer'.::

            possible_candidates = ('SIS 3301', 'SIS crate')
        """
        # possible_candidates is a hierarchical tuple of all digitizers
        # such that the first found digitizer is assumed to be the main
        # digitizer
        possible_candidates = ('SIS 3301', 'SIS crate')
        digi = None
        try:
            for key in possible_candidates:
                if key in self.__digitizers:
                    digi = self.__digitizers[key]
                    break
        except TypeError:
            # catch if __digitizers is None
            pass

        return digi
