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
import numpy as np
import os

from abc import (ABC, abstractmethod)
from typing import List
from warnings import warn

from .clparse import CLParse


class hdfMap_control_template(ABC):
    # noinspection PySingleQuotedDocstring
    '''
    Template class for all control mapping classes to inherit from.

    Any inheriting class should define :code:`__init__` as::

        def __init__(self, group: h5py.Group):
            """
            :param group: HDF5 group object
            """
            # initialize
            hdfMap_control_template.__init__(self, control_group)

            # define control type
            # - control types can be 'motion', 'power', 'waveform', or
            #   'timing'
            #
            self.info['contype'] = 'motion'

            # populate self.configs
            self._build_configs()

    .. note::

        Any method that raises a :exc:`NotImplementedError` is intended
        to be overwritten by the inheriting class.
    '''
    def __init__(self, group: h5py.Group):
        """
        :param group: the control device HDF5 group object
        """
        # condition group arg
        if isinstance(group, h5py.Group):
            self._control_group = group
        else:
            raise TypeError('arg `group` is not of type h5py.Group')

        # define _info attribute
        self._info = {
            'group name': os.path.basename(group.name),
            'group path': group.name,
            'contype': NotImplemented,
        }

        # initialize configuration dictionary
        self._configs = {}
        """
        Configuration dictionary of HDF5 control device. This dictionary
        is slightly polymorphic depending on the control type.  That is,
        there are some core items that exist for all control types and
        some that are control type dependent.
        
        The core items for :code:`configs`::
        
            configs = {
                'config names': [str, ], # list of configuration names
                'nControlled': int, # number of controlled probes and/or
                                    # utilized control setups
                                'dataset fields':
                    [(str,              # name of dataset field
                      dtype), ],        # numpy dtype of field
                'dset field to numpy field':
                    [(str,      # name of dataset field
                                # ~ if a tuple like (str, int) then this
                                #   indicates that the dataset field is
                                #   linked to a command list 
                      str,      # name of numpy field that will be used
                                # by hdfReadControl
                      int), ]   # numpy array index for which the
                                # dataset entry will be mapped into
            }
        
        For :code:`info['contype'] == 'motion'`:
        
        .. code-block:: python
            
            # core config items
            configs = {
                'motion list': [str, ], # list of motion list names
                'probe list': [str, ],  # list of probe names
                'nControlled': int,     # number of controlled probes
                'dataset fields':
                    [(str,              # name of dataset field
                      dtype), ],        # numpy dtype of field
                'dset field to numpy field':
                    [(str,      # name of dataset field
                                # ~ if a tuple like (str, int) then this
                                #   indicates that the dataset field is
                                #   linked to a command list 
                      str,      # name of numpy field that will be used
                                # by hdfReadControl
                      int), ]   # numpy array index for which the
                                # dataset entry will be mapped into
            }
            
            # specific motion config items
            for name in configs['motion list']:
                configs[name] = motion_dict
            
            # motion_dict format
            motion_dict = {
                'delta': (dx, dy, dz),  # step-size in xyz
                'center': (x0, y0, z0), # origin
                'npoints': (nx, ny, nz) # number of positions in xyz
            }
            
            # specific probe config items
            for name in configs['probe list']:
                configs[name] = probe_dict
            
            # probe_dict format
            probe_dict = {
                'receptacle': int, # probe drive receptacle number
                                   # - used as unique specifier
                'port': int        # LaPD port the probe drive was
                                   # connected to
            }
            
        
        For :code:`info['contype'] in ['waveform', 'power']`:
        
        .. code-block:: python
        
            # core config items
            configs = {
                'config names': [str, ], # list of control device 
                                         # config names
                'nControlled': int,      # number of controlled probes
                'dataset fields':
                    [(str,               # name of dataset field
                      dtype), ],         # numpy dtype of field
                'dset field to numpy field':
                    [(str,      # name of dataset field
                                # ~ if a tuple like (str) or (str, int)
                                #   then this indicates that the dataset
                                #   field is linked to a command list 
                      str,      # name of numpy field that will be used
                                # by hdfReadControl
                      int), ]   # numpy array index for which the
                                # dataset entry will be mapped into
            }
            
            # configuration specific items
            for name in configs['config names']:
                configs[name] = {
                    'IP address': str, # control device IP address
                    'command list': [] # typically a list of floating
                                       # point variables whose values
                                       # correspond to the property
                                       # controlled by the device
                                       # - the list index corresponds to
                                       #   the command list value in the
                                       #   control device dataset
                                       # - the list can be polymorphic
                                       #   to the property type
                                       #   controlled
                }
        """

    @property
    def configs(self) -> dict:
        """
        Dictionary containing all the relevant mapping information to
        translate the HDF5 data locations for the
        :mod:`bapsflib.lapd` module.

        .. note::

            While this dictionary has some required structure to it,
            the dictionary is also semi-polymorphic depending on the
            control device it is mapping.
        """
        # TODO: fill out docstring for attribute `configs`
        # TODO: format of configs needs to be solidified
        return self._configs

    @property
    def contype(self) -> str:
        """
        control device type (:code:`'motion'`, :code:`'power'`,
        :code:`'timing'`, or :code:`'waveform'` )
        """
        return self._info['contype']

    @property
    def dataset_names(self) -> List[str]:
        """list of names of the HDF5 datasets in the control group"""
        dnames = [name
                  for name in self.group
                  if isinstance(self.group[name], h5py.Dataset)]
        return dnames

    @property
    def group(self) -> h5py.Group:
        """Instance of the HDF5 Control Device group"""
        return self._control_group

    @property
    def has_command_list(self) -> bool:
        """
        :return: :code:`True` if dataset utilizes a command list
        """
        # TODO: do this based on inheriting template and enforce with tests
        has_cl = False
        for config_name in self._configs:
            if 'command list' in self._configs[config_name]:
                has_cl = True
                break
        return has_cl

    @property
    def info(self) -> dict:
        """
        Control device dictionary of meta-info. For example, ::

            info = {
                'group name': 'Control',
                'group path': '/foo/bar/Control',
                'contype': 'motion',
            }
        """
        return self._info

    @property
    def one_config_per_dset(self) -> bool:
        """
        :code:'True' if each control configuration has itsown dataset
        """
        n_dset = len(self.dataset_names)
        n_configs = len(self._configs)
        return True if n_dset == n_configs else False

    @property
    def subgroup_names(self) -> List[str]:
        """list of names of the HDF5 sub-groups in the control group"""
        sgroup_names = [name
                        for name in self.group
                        if isinstance(self.group[name], h5py.Group)]
        return sgroup_names

    @property
    def device_name(self) -> str:
        """Name of Control device"""
        return self._info['group name']

    @abstractmethod
    def construct_dataset_name(self, *args) -> str:
        """
        Constructs the dataset name corresponding to the input
        arguments.

        :return: name of dataset
        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @abstractmethod
    def _build_configs(self):
        """
        Gathers the necessary metadata and fills :data:`configs`.

        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError


class hdfMap_control_cl_template(hdfMap_control_template):
    """
    A modified :class:`hdfMap_control_template` template class for
    mapping control devices that record around the concept of a
    **command list**.

    Any inheriting class should define :code:`__init__` as::

        def __init__(self, control_group):
            # initialize
            hdfMap_control_cl_template.__init__(self, control_group)

            # define control type
            # - control types can be 'motion', 'power', 'waveform'
            #
            self.info['contype'] = 'waveform'

            # define known command list RE patterns
            self._cl_re_patterns.exten([
                r'(?P<FREQ>(\bFREQ\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))'
            ])

            # populate self.configs
            # - the method _build_configs contains the code to build
            #   the self.configs dictionary
            #
            self._build_configs()

    .. note::

        Any method that raises a :exc:`NotImplementedError` is intended
        to be overwritten by the inheriting class.
    """
    def __init__(self, group):
        """
        :param group: the control HDF5 group
        :type group: :class:`h5py.Group`
        """
        hdfMap_control_template.__init__(self, group)

        # initialize internal 'command list' regular expression (RE)
        # patterns
        self._cl_re_patterns = []
        """List of common RE patterns."""

    @abstractmethod
    def _default_state_values_dict(self, config_name: str) -> dict:
        """
        Returns the default :code:`'state values'` dictionary for
        configuration *config_name*.

        :param str config_name: configuration name
        :raise: :exc:`NotImplementedError`

        .. code-block:: python
            :caption: Example of declaration

            # define default dict
            default_dict = {
                'command': {
                    'dset paths':
                        self._configs[config_name]['dese paths'],
                    'dset field': ('Command index', ),
                    'cl pattern': None,
                    'command list': np.array(
                        self._configs[config_name]['command list']),
                    'shape': (),
                }
            }
            default_dict['command']['dtype'] = \\
                default_dict['command']['command list'].dtype

            # return
            return default_dict

        """
        raise NotImplementedError

    def _construct_state_values_dict(self,
                                     config_name: str,
                                     patterns: List[str]) -> dict:
        """
        Returns a dictionary for
        :code:`configs[config_name]['state values]` based on the
        supplied RE patterns. :code:`None` is returned if the
        construction failed.

        :param str config_name: configuration name
        :param patterns: list of RE pattern strings
        :type patterns: list(str)
        """
        # -- check requirements exist before continuing             ----
        # get dataset
        dset_path = self._configs[config_name]['dset paths']
        dset = self.group.get(dset_path)

        # ensure 'Command index' is a field
        if 'Command index' not in dset.dtype.names:
            warn("Dataset '{}' does NOT have ".format(dset_path)
                 + "'Command index' field")
            return {}

        # ensure 'Command index' is a field of scalars
        if dset.dtype['Command index'].shape != () or \
                not np.issubdtype(dset.dtype['Command index'].type,
                                  np.integer):
            warn("Dataset '{}' 'Command index' ".format(dset_path)
                 + "field is NOT a column of integers")
            return {}

        # -- apply RE patterns to 'command list'                    ----
        success, sv_dict = \
            self.clparse(config_name).apply_patterns(patterns)

        # regex was unsuccessful, return alt_dict
        if not success:
            return {}

        # -- complete `sv_dict` before return                       ----
        # 1. 'command list' and 'cl str' are tuples from clparse
        # 2. add 'dset paths'
        # 3. add 'dset field'
        # 4. add 'shape'
        # 5. 'dtype' defined by clparse.apply_patterns
        #
        for state in sv_dict:
            # add additional keys
            sv_dict[state]['dset paths'] = \
                self._configs[config_name]['dset paths']
            sv_dict[state]['dset field'] = ('Command index',)
            sv_dict[state]['shape'] = ()

        # return
        return sv_dict

    def clparse(self, config_name: str) -> CLParse:
        """
        Return instance of
        :class:`~bapsflib.lapd.controls.clparse.CLParse`
        for `config_name`.

        :param str config_name: configuration name
        """
        # retrieve command list
        cl = self._configs[config_name]['command list']

        # define clparse and return
        return CLParse(cl)

    def reset_state_values_config(self, config_name: str,
                                  apply_patterns=False):
        """
        Reset the :code:`configs[config_name]['state values']`
        dictionary.

        :param str config_name: configuration name
        :param bool apply_patterns: Set :code:`False` (DEFAULT) to
            reset to :code:`_default_state_values_dict(config_name)`.
            Set :code:`True` to rebuild dict using
            :attr:`_cl_re_patterns`.
        """
        if apply_patterns:
            # get sv_dict dict
            sv_dict = self._construct_state_values_dict(
                config_name, self._cl_re_patterns)
            if not bool(sv_dict):
                sv_dict = self._default_state_values_dict(config_name)
        else:
            # get default dict
            sv_dict = self._default_state_values_dict(config_name)

        # reset config
        self._configs[config_name]['state values'] = sv_dict

    def set_state_values_config(self, config_name: str,
                                patterns: List[str]):
        """
        Rebuild and set
        :code:`configs[config_name]['state values']` based on the
        supplied RE *patterns*.

        :param str config_name: configuration name
        :param patterns: list of RE strings
        """

        # construct dict for 'state values' dict
        sv_dict = self._construct_state_values_dict(config_name,
                                                    patterns)

        # update 'state values' dict
        if not bool(sv_dict):
            # do nothing since default parsing was unsuccessful
            warn("RE parsing of 'command list' was unsuccessful, "
                 "doing nothing")
        else:
            self._configs[config_name]['state values'] = sv_dict
