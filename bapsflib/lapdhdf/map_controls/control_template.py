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
        self.config = {
            'motion list': NotImplemented,
            'probe list': NotImplemented,
            'command list': NotImplemented,
            'nControlled': NotImplemented,
            'dataset fields': NotImplemented,
            'dset field to numpy field': NotImplemented
        }
        """
        .. code-block: python
        
            config = {
                'motion list': [str, ],
                'motion list name': motion_dict,
                ...
                'probe list': [str, ],
                'probe name: probe_dict,
                ...
                'command list': [],
                'nControlled': int,
                'dataset fields': [(key, dtype), ],
                'dset field to numpy field': [
                    ('dset field name', 
                     'numpy filed name',
                      int of numpy index), ]
            }
            
            motion_dict = {
                delta: (dx, dy ,dz),
                center: (x0, y0, z0),
                npoints: (nx, ny, nz)
            }
            
            probe_dict = {
                receptacle: int,
                port: int
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

    @abstractmethod
    def construct_dataset_name(self, *args):
        raise NotImplementedError

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

    def _verify_map(self):
        # ---- verify self.info ----
        if self.info['contype'] == NotImplemented:
            # 'contype' must be defined
            errstr = "self.info['contype'] must be defined as:\n" \
                     "  'motion', 'freq', or 'power'"
            raise NotImplementedError(errstr)
        elif self.info['contype'] not in ['motion', 'freq', 'power']:
            # 'contype' must be one of specified type
            errstr = "self.info['contype'] must be defined as:\n" \
                     "  'motion', 'freq', or 'power'"
            raise NotImplementedError(errstr)

        # ---- verity self.config ----
        # 'dataset fields' must be defined
        if 'dataset fields' not in self.config:
            errstr = "self.config['dataset fields'] must be defined " \
                     "as:\n  [('field name', dtype), ]"
            raise NotImplementedError(errstr)
        elif self.config['dataset fields'] == NotImplemented:
            errstr = "self.config['dataset fields'] must be defined " \
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
        #   self.config['dset field to numpy field'][i] = (
        #       str, # dataset field name
        #       str, # corresponding structured numpy field name
        #       int) # index of structured numpy field
        #
        #   For example, the '6K Compumotor would look like...
        #       self.config['dset field to numpy'] = [
        #           ('x', 'xyz', 0),
        #           ('y', 'xyz', 1),
        #           ('z', 'xyz', 2)]
        #
        key = 'dset field to numpy field'
        if key not in self.config:
            raise NotImplementedError
        elif self.config[key] == NotImplemented:
            raise NotImplementedError
        elif type(self.config[key]) is not list:
            errstr = "self.config['dset field to numpy field] must " \
                     + "be a list of 3-element tuples"
            raise Exception(errstr)
        elif not all(isinstance(val, tuple)
                     for val in self.config[key]):
            errstr = "self.config['dset field to numpy field] must " \
                     + "be a list of 3-element tuples"
            raise Exception(errstr)
        elif not all(len(val) == 3 for val in self.config[key]):
            errstr = "self.config['dset field to numpy field] must " \
                     + "be a list of 3-element tuples"
            raise Exception(errstr)
        else:
            err = False
            dset_fields = [name
                           for name, dftype
                           in self.config['dataset fields']]
            for dfname, npfname, npi in self.config[key]:
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
                errstr = "self.config['dset field to numpy field] must " \
                         + "be a list of 3-element tuples"
                raise Exception(errstr)

        # contype == 'motion' specific verification
        if self.contype == 'motion':
            # verify 'motion list'
            if 'motion list' not in self.config:
                # 'motion list' exists
                errstr = "self.config['motion list'] must be defined"
                raise NotImplementedError(errstr)
            elif self.config['motion list'] == NotImplemented:
                # 'motion list' is defined
                errstr = "self.config['motion list'] must be defined"
                raise NotImplementedError(errstr)
            else:
                # each 'motion list' must have its own config
                for name in self.config['motion list']:
                    if name not in self.config:
                        errstr = "must defined self.config['motion " \
                                 "name'] for each motion list in " \
                                 "self.config['motion list'] = " \
                                 "[motion name, ]"
                        raise NotImplementedError(errstr)

            # verify 'probe list'
            if 'probe list' not in self.config:
                # 'probe list' exists
                errstr = "self.config['probe list'] must be defined"
                raise NotImplementedError(errstr)
            elif self.config['probe list'] == NotImplemented:
                # 'probe list' is defined
                errstr = "self.config['probe list'] must be defined"
                raise NotImplementedError(errstr)
            else:
                # each 'probe list' must have its own config
                for name in self.config['probe list']:
                    if name not in self.config:
                        errstr = "must defined self.config['probe " \
                                 "name'] for each probe in " \
                                 "self.config['probe list'] = " \
                                 "[probe name, ]"
                        raise NotImplementedError(errstr)

            # delete 'command list' if present
            if 'command list' in self.config:
                del(self.config['command list'])

        # verify all other contypes
        if self.contype != 'motion':
            # remove 'motion list'
            if 'motion list' in self.config:
                # remove 'motion list' children
                for name in self.config['motion list']:
                    if name in self.config:
                        del(self.config[name])

                # remove 'motion list'
                del(self.config['motion list'])

            # remove 'probe list'
            if 'probe list' in self.config:
                # remove 'probe list' children
                for name in self.config['probe list']:
                    if name in self.config:
                        del (self.config[name])

                # remove 'motion list'
                del (self.config['probe list'])

            # verify 'command list'
            if 'command list' not in self.config:
                # 'command list' exists
                errstr = "self.config['command list'] must be defined"
                raise NotImplementedError(errstr)
            elif self.config['command list'] == NotImplemented:
                # 'motion list' is defined
                errstr = "self.config['command list'] must be defined"
                raise NotImplementedError(errstr)
