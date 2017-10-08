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

from abc import abstractmethod


class hdfMap_control_template(object):
    """
    A template class for all control mapping classes to inherit from.

    .. note::

        Any method that raises a :exc:`NotImplementedError` is intended
        to be overwritten by the inheriting class.
    """
    def __init__(self, control_group):
        """
        :param control_group: the control HDF5 group
        :type control_group: :mod:`h5py.Group`
        """

        # condition control_group arg
        if isinstance(control_group, h5py.Group):
            self.__control_group = control_group
        else:
            raise TypeError('arg digi_group is not of type h5py.Group')

        # define info attribute
        self.info = {'group name': control_group.name.split('/')[-1],
                     'group path': control_group.name,
                     'contype': NotImplemented}
        """
        Information dict of control HDF5 Group

        .. code-block:: python

            info = {
                'group name': str, # name of control group
                'group path': str  # full path to control group
            }
        """

        # initialize configuration dictionary
        self.config = {}
        """
        .. code-block: python
        
            config = {
                'motion list': [str, ],
                'command list': [],
                'data fields': (key, dtype)
            }
        """

    @property
    def control_group(self):
        """
        :return: HDF5 control group
        :rtype: :mod:`h5py.Group`
        """
        return self.__control_group

    @property
    def contype(self):
        """
        :return: Type of control
        :rtype: str
        """
        return self.info['contype']

    @property
    def sgroup_names(self):
        sgroup_names = [name
                        for name in self.control_group
                        if isinstance(self.control_group[name],
                                      h5py.Group)]
        return sgroup_names

    @property
    def dataset_names(self):
        dnames = [name
                  for name in self.control_group
                  if isinstance(self.control_group[name], h5py.Dataset)]
        return dnames

    @abstractmethod
    def _build_config(self):
        raise NotImplementedError
