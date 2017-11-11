# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
# TODO: determine a default structure for all digitizer classes
#
import h5py

from .sis3301 import hdfMap_digi_sis3301
from .siscrate import hdfMap_digi_siscrate


class hdfMap_digitizers(dict):
    """
    A dictionary that contains mapping objects for all the discovered
    digitizers in the HDF5 data group.  The dictionary keys are the
    discovered digitizer names.

    For example,

        >>> dmaps = hdfMap_digitizers(data_group)
        >>> dmaps['SIS 3301']
        OUT: <bapsflib.lapdhdf.map_digitizers.sis3301.hdfMap_digi_sis3301>
    """
    _defined_digitizer_mappings = {
        'SIS 3301': hdfMap_digi_sis3301,
        'SIS crate': hdfMap_digi_siscrate}
    """
    Dictionary containing references to the defined (known) digitizer 
    mapping classes.
    """

    def __init__(self, data_group):
        """
        :param data_group: HDF5 (data) group that contains the digitizer
            groups
        :type data_group: :class:`h5py.Group`
        """

        # condition data_group arg
        if type(data_group) is not h5py.Group:
            raise TypeError('data_group is not of type h5py.Group')

        # store HDF5 data group instance
        self.__data_group = data_group

        # all data_group subgroups
        # - each of these subgroups can fall into one of four 'LaPD
        #   data types'
        #   1. data sequence
        #   2. digitizer groups (known)
        #   3. controls (known)
        #   4. unknown
        #
        #: list of all group names in the HDF5 data group
        self.data_group_subgnames = []
        for name in data_group:
            if type(data_group[name]) is h5py.Group:
                self.data_group_subgnames.append(name)

        # Build the self dictionary
        dict.__init__(self, self.__build_dict)

    # @property
    # def data_group(self):
    #     """
    #     :return: instance of the HDF5 data group containing the
    #         digitizers
    #     :rtype: :mod:`h5py.Group`
    #     """
    #     return self.__data_group

    @property
    def predefined_digitizer_groups(self):
        """
        :return: list of the predefined digitizer group names
        :rtype: list(str)
        """
        return list(self._defined_digitizer_mappings)

    @property
    def __build_dict(self):
        """
        Discovers the HDF5 digitizers and builds the dictionary
        containing the digitizer mapping objects.  This is the
        dictionary used to initialize :code:`self`.

        :return: digitizer mapping dictionary
        :rtype: dict
        """
        digi_dict = {}
        try:
            for name in self.data_group_subgnames:
                if name in self._defined_digitizer_mappings:
                    digi_dict[name] = \
                        self._defined_digitizer_mappings[name](
                            self.__data_group[name])
        except TypeError:
            pass

        return digi_dict
