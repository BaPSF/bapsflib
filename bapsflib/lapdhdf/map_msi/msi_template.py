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

from abc import ABC, abstractmethod


class hdfMap_msi_template(ABC):
    """
    Template class for all MSI diagnostic mapping classes to inherit
    from.

    Any inheriting class should define :code:`__init__` as::

        def __init__(self, diag_group):
            # initialize
            hdfMap_msi_template.__init__(self, diag_group)

            # populate self.configs
            self._build_configs()

    .. note::

        Any method that raises a :exc:`NotImplementedError` is intended
        to be overwritten by the inheriting class.
    """
    def __init__(self, diag_group):
        """
        :param diag_group: the MSI diagnostic HDF5 group
        :type diag_group: :class:`h5py.Group`
        """
        # condition diag_group arg
        if isinstance(diag_group, h5py.Group):
            self.__diag_group = diag_group
        else:
            raise TypeError('arg diag_group is not of type h5py.Group')

        # define info attribute
        self.info = {
            'group name': diag_group.name.split('/')[-1],
            'group path': diag_group.name
        }
        """
        Information dict for the MSI diagnostic HDF5 group::
        
            info = {
                'group name': str, # name of diagnostic group
                'group path': str  # full path to diagnostic group
            }
        """

        # initialize self.configs
        self.configs = {}

    @property
    def diagnostic_name(self):
        """Name of MSI diagnostic"""
        return self.info['group name']

    @property
    def group(self):
        """MSI diagnostic group"""
        return self.__diag_group

    @abstractmethod
    def _build_configs(self):
        """
        Gathers the necessary metadata and fills :data:`configs`
        :raises: :exc:`NotImplementedError`
        """
        raise NotImplementedError
