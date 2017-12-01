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

from abc import ABC, abstractmethod


class hdfMap_control_template(ABC):
    """
    Template class for all control mapping classes to inherit from.

    Any inheriting class should define :code:`__init__` as::

        def __init__(self, control_group):
            # initialize
            hdfMap_control_template.__init__(self, control_group)

            # define control type
            # - control types can be 'motion', 'power', 'waveform'
            #
            self.info['contype'] = 'motion'

            # populate self.configs
            # - the method _build_configs contains the code to build
            #   the self.configs dictionary
            #
            self._build_configs()

            # verify key class attributes and methods
            # - _verify_map() is a template method that ensures
            #   self.info and self.configs are properly constructed so
            #   that the rest of bapsflib.lapdhdf can utilized the
            #   mapping.
            #
            self._verify_map()

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
        if type(control_group) is h5py.Group:
            self.__control_group = control_group
        else:
            raise TypeError('arg digi_group is not of type h5py.Group')

        # define info attribute
        self.info = {'group name': control_group.name.split('/')[-1],
                     'group path': control_group.name,
                     'contype': NotImplemented}
        """
        Information dictionary of HDF5 control device

        .. code-block:: python

            info = {
                'group name': str, # name of control group
                'group path': str, # full path to control group
                'contype': str     # control device type
            }
        """

        # initialize configuration dictionary
        # TODO: format of configs needs to be solidified
        #
        # 'motion list': NotImplemented,
        # 'probe list': NotImplemented,
        # 'config names': NotImplemented,
        # 'nControlled': NotImplemented,
        # 'dataset fields': NotImplemented,
        # 'dset field to numpy field': NotImplemented
        self.configs = {}
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
    def contype(self):
        """
        :return: Type of control device (:code:`'motion'`,
            :code:`'waveform'`, or :code:`'power'`)
        :rtype: str
        """
        return self.info['contype']

    @property
    def dataset_names(self):
        """
        :return: list of names of the HDF5 datasets in the control group
        :rtype: [str, ]
        """
        dnames = [name
                  for name in self.group
                  if type(self.group[name]) is h5py.Dataset]
        return dnames

    @property
    def has_command_list(self):
        """
        :return: :code:`True` if dataset utilizes a command list
        :rtype: bool
        """
        has_cl = False
        for name in self.configs['config names']:
            if 'command list' in self.configs[name]:
                has_cl = True
                break
        return has_cl

    @property
    def group(self):
        """
        :return: HDF5 control device group
        :rtype: :class:`h5py.Group`
        """
        return self.__control_group

    @property
    def sgroup_names(self):
        """
        :return: list of names of the HDF5 groups in the control group
        :rtype: [str, ]
        """
        sgroup_names = [name
                        for name in self.group
                        if type(self.group[name]) is h5py.Group]
        return sgroup_names

    @abstractmethod
    def construct_dataset_name(self, *args):
        """
        Constructs the dataset name corresponding to the input
        arguments.

        :return: name of dataset
        :rtype: str
        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @property
    def unique_specifiers(self):
        """
        :return: list of unique specifiers for the control device.
            Define as :code:`None` if there are none.
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

    def _verify_map(self):
        """
        This method verifies the dictionaries self.info and self.configs
        to ensure that they are formatted properly for the rest of the
        :class:`bapsflib.lapdhdf` package.
        """
        # ---- verify self.info ----
        if self.info['contype'] == NotImplemented:
            # 'contype' must be defined
            errstr = "self.info['contype'] must be defined as:\n" \
                     "  'motion', 'waveform', or 'power'"
            raise NotImplementedError(errstr)
        elif self.info['contype'] not in ['motion',
                                          'waveform',
                                          'power']:
            # 'contype' must be one of specified type
            errstr = "self.info['contype'] must be defined as:\n" \
                     "  'motion', 'waveform', or 'power'"
            raise NotImplementedError(errstr)

        # ---- verity self.configs ----
        # 'dataset fields' must be defined
        if 'dataset fields' not in self.configs:
            errstr = "self.configs['dataset fields'] must be defined " \
                     "as:\n  [('field name', dtype), ]"
            raise NotImplementedError(errstr)
        elif self.configs['dataset fields'] == NotImplemented:
            errstr = "self.configs['dataset fields'] must be defined " \
                     "as:\n  [('field name', dtype), ]"
            raise NotImplementedError(errstr)

        # 'dset field to numpy field' must be defined
        # - each 'dataset field' needs a mapping to a structured numpy
        #   field for hdfReadControl
        # - 'dset field to numpy field' is a list of 3-element tuples
        #   where each entry in the list corresponds to a dataset field
        #   name
        # - the 3-element tuple must follow the format:
        #
        #   self.configs['dset field to numpy field'][i] = (
        #       str, # dataset field name
        #       str, # corresponding structured numpy field name
        #       int) # index of structured numpy field
        #
        #   For example, the '6K Compumotor would look like...
        #       self.configs['dset field to numpy'] = [
        #           ('x', 'xyz', 0),
        #           ('y', 'xyz', 1),
        #           ('z', 'xyz', 2)]
        #
        key = 'dset field to numpy field'
        if key not in self.configs:
            raise NotImplementedError
        elif self.configs[key] == NotImplemented:
            raise NotImplementedError
        elif type(self.configs[key]) is not list:
            errstr = "self.configs['dset field to numpy field] must " \
                     + "be a list of 3-element tuples"
            raise Exception(errstr)
        elif not all(isinstance(val, tuple)
                     for val in self.configs[key]):
            errstr = "self.configs['dset field to numpy field] must " \
                     + "be a list of 3-element tuples"
            raise Exception(errstr)
        elif not all(len(val) == 3 for val in self.configs[key]):
            errstr = "self.configs['dset field to numpy field] must " \
                     + "be a list of 3-element tuples"
            raise Exception(errstr)
        else:
            err = False
            dset_fields = [name
                           for name, dftype
                           in self.configs['dataset fields']]
            for dfname, npfname, npi in self.configs[key]:
                if dfname not in dset_fields:
                    err = True
                    break
                elif type(npfname) is not str:
                    err = True
                    break
                elif type(npi) is not int:
                    err = True
                    break
            if err:
                errstr = "self.configs['dset field to numpy field] " \
                         + "must be a list of 3-element tuples"
                raise Exception(errstr)

        # contype == 'motion' specific verification
        if self.contype == 'motion':
            # verify 'motion list'
            if 'motion list' not in self.configs:
                # 'motion list' exists
                errstr = "self.configs['motion list'] must be defined"
                raise NotImplementedError(errstr)
            elif self.configs['motion list'] == NotImplemented:
                # 'motion list' is defined
                errstr = "self.configs['motion list'] must be defined"
                raise NotImplementedError(errstr)
            else:
                # each 'motion list' must have its own config
                for name in self.configs['motion list']:
                    if name not in self.configs:
                        errstr = "must defined self.configs['motion " \
                                 "name'] for each motion list in " \
                                 "self.configs['motion list'] = " \
                                 "[motion name, ]"
                        raise NotImplementedError(errstr)

            # verify 'probe list'
            if 'probe list' not in self.configs:
                # 'probe list' exists
                errstr = "self.configs['probe list'] must be defined"
                raise NotImplementedError(errstr)
            elif self.configs['probe list'] == NotImplemented:
                # 'probe list' is defined
                errstr = "self.configs['probe list'] must be defined"
                raise NotImplementedError(errstr)
            else:
                # each 'probe list' must have its own config
                for name in self.configs['probe list']:
                    if name not in self.configs:
                        errstr = "must defined self.configs['probe " \
                                 "name'] for each probe in " \
                                 "self.configs['probe list'] = " \
                                 "[probe name, ]"
                        raise NotImplementedError(errstr)

            # delete 'config names' if present
            if 'config names' in self.configs:
                del self.configs['config names']

        # verify all other contypes
        if self.contype != 'motion':
            # remove 'motion list'
            if 'motion list' in self.configs:
                # remove 'motion list' children
                for name in self.configs['motion list']:
                    if name in self.configs:
                        del(self.configs[name])

                # remove 'motion list'
                del(self.configs['motion list'])

            # remove 'probe list'
            if 'probe list' in self.configs:
                # remove 'probe list' children
                for name in self.configs['probe list']:
                    if name in self.configs:
                        del (self.configs[name])

                # remove 'motion list'
                del (self.configs['probe list'])

            # verify 'command list'
            # if 'command list' not in self.configs:
            #     # 'command list' exists
            #     errstr = "self.configs['command list'] must be " \
            #              "defined"
            #     raise NotImplementedError(errstr)
            # elif self.configs['command list'] == NotImplemented:
            #     # 'motion list' is defined
            #     errstr = "self.configs['command list'] must be " \
            #              "defined"
            #     raise NotImplementedError(errstr)
