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

import h5py


class hdfMap_controls(dict):
    """
    Creates a dictionary that contains mapping instances for all the
    discovered probe controls in the HDF5 data group.
    """
    _defined_control_mappings = {
        '6K Compumotor': None}
    """
    A dictionary containing references to the defined control mapping
    classes
    """

    def __init__(self, data_group):
        """

        :param data_group: the HDF5 group that contains the control
            groups
        :type data_group: :mod:`h5py.Group`
        """

        # condition data_group arg
        if not isinstance(data_group, h5py.Group):
            raise TypeError('data_group is not of type h5py.Group')

        self.__data_group = data_group

        # Build the self dictionary
        dict.__init__(self, self.__build_dict)

    @property
    def data_group(self):
        """
        :return: instance of the HDF5 data group containing the
            digitizers
        :rtype: :mod:`h5py.Group`
        """
        return self.__data_group

    @property
    def predefined_control_groups(self):
        """
        :return: list of the predefined control group names
        :rtype: list(str)
        """
        return list(self._defined_control_mappings.keys())

    @property
    def __build_dict(self):
        """
        Builds a dictionary containing mapping instances of all the
        discovered probe controls in the data group.

        :return: control mapping dictionary
        """
        control_dict = {}
        return control_dict
