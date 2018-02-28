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

import h5py

from .sixk import hdfMap_control_6k
from .waveform import hdfMap_control_waveform

class hdfMap_controls(dict):
    """
    A dictionary that contains mapping objects for all the discovered
    control devices in the HDF5 data group.  The dictionary keys are
    the names of the discovered control devices.

    For example,

        >>> cmaps = hdfMap_controls(data_group)
        >>> cmaps['6K Compumotor']
        Out: <bapsflib.lapdhdf.map_controls.sixk.hdfMap_control_6k>
    """
    _defined_control_mappings = {
        '6K Compumotor': hdfMap_control_6k,
        'Waveform': hdfMap_control_waveform}
    """
    Dictionary containing references to the defined (known) control
    device mapping classes.
    """

    def __init__(self, data_group):
        """
        :param data_group: HDF5 (data) group that contains the control
            device groups
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
        for item in data_group:
            if type(data_group[item]) is h5py.Group:
                self.data_group_subgnames.append(item)

        # Build the self dictionary
        dict.__init__(self, self.__build_dict)

    # @property
    # def data_group(self):
    #    """
    #    :return: instance of the HDF5 data group containing the
    #        digitizers
    #    :rtype: :mod:`h5py.Group`
    #    """
    #    return self.__data_group

    @property
    def predefined_control_groups(self):
        """
        :return: list of the predefined control device group names
        :rtype: list(str)
        """
        return list(self._defined_control_mappings.keys())

    @property
    def __build_dict(self):
        """
        Discovers the HDF5 control devices and builds the dictionary
        containing the control device mapping objects.  This is the
        dictionary used to initialize :code:`self`.

        :return: control device mapping dictionary
        :rtype: dict
        """
        control_dict = {}
        for sg_name in self.data_group_subgnames:
            if sg_name in self._defined_control_mappings:
                control_dict[sg_name] = \
                    self._defined_control_mappings[sg_name](
                        self.__data_group[sg_name])
        return control_dict
