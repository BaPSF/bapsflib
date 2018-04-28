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
import numpy as np

from .control_template import hdfMap_control_template


class hdfMap_control_6k(hdfMap_control_template):
    """
    Mapping module for control device '6K Compumotor'.
    """
    def __init__(self, control_group):
        hdfMap_control_template.__init__(self, control_group)

        # define control type
        self._info['contype'] = 'motion'

        # populate self.configs
        self._build_configs()

    def _build_configs(self):
        # build order:
        #  1. build a private motion list dictionary
        #  2. build local probe list dictionary
        #  3. build configs dict
        #
        # TODO: HOW TO ADD MOTION LIST TO DICT

        # build 'motion list' and 'probe list'
        self._motion_lists = {}
        probe_lists = {}
        for name in self.sgroup_names:
            is_ml, ml_name, ml_config = self._parse_motionlist(name)
            if is_ml:
                # build 'motion list'
                self._motion_lists[ml_name] = ml_config
            else:
                is_p, p_name, p_config = self._parse_probelist(name)
                if is_p:
                    # build 'probe list'
                    probe_lists[p_name] = p_config

        # build configuration dictionaries
        # - the receptacle number is the config_name
        # - each probe is one-to-one with receptacle number
        #
        for pname in probe_lists:
            # define configuration name
            config_name = probe_lists[pname]['receptacle']

            # ---- start assigning values to _configs               ----
            #  assign non-critical values
            self._configs[config_name] = {
                'probe name': pname,
                'port': probe_lists[pname]['port'],
                'receptacle': probe_lists[pname]['receptacle'],
                'motion lists': {}
            }

            # get dataset
            dset = self.group[self.construct_dataset_name(config_name)]

            # assign 'dset paths'
            self._configs[config_name]['dset paths'] = dset.name

            # ---- define 'shotnum'                                 ----
            # initialize
            self._configs[config_name]['shotnum'] = {
                'dset paths': self._configs[config_name]['dset paths'],
                'dset field': 'Shot number',
                'shape': dset.dtype['Shot number'].shape,
                'dtype': np.int32
            }

            # ---- define 'state values'                            ----
            self._configs[config_name]['state values'] = {
                'xyz': {
                    'dset paths':
                        self._configs[config_name]['dset paths'],
                    'dset field': ('x', 'y', 'z'),
                    'shape': (3,),
                    'dtype': np.float64
                },
                'ptip_rot_theta': {
                    'dset paths':
                        self._configs[config_name]['dset paths'],
                    'dset field': ('theta',),
                    'shape': (),
                    'dtype': np.float64
                },
                'ptip_rot_phi': {
                    'dset paths':
                        self._configs[config_name]['dset paths'],
                    'dset field': ('phi',),
                    'shape': (),
                    'dtype': np.float64
                },
            }

        # indicate build was successful
        self._build_successful = True

    def construct_dataset_name(self, *args):
        # The first arg passed is assumed to be the receptacle number.
        # If none are passed and there is only one receptacle deployed,
        # then the deployed receptacle is assumed.

        # Set receptacle value
        err = False
        if len(args) == 0:
            if len(self.list_receptacles) == 1:
                # assume only receptacle
                receptacle = self.list_receptacles[0]
            else:
                err = True
        elif len(args) >= 1:
            receptacle = args[0]
            if receptacle is None:
                if len(self.list_receptacles) == 1:
                    # assume only receptacle
                    receptacle = self.list_receptacles[0]
                else:
                    err = True
            elif receptacle not in self.list_receptacles:
                err = True
        else:
            err = True
        if err:
            raise ValueError('A valid receptacle number needs to be '
                             'passed: {}'.format(self.list_receptacles))

        # Find matching probe to receptacle
        # - note that probe naming in the HDF5 are not consistent, this
        #   is why dataset name is constructed based on receptacle and
        #   not probe name
        #
        pname = self._configs[receptacle]['probe name']

        # Construct dataset name
        dname = 'XY[{0}]: {1}'.format(receptacle, pname)

        return dname

    @property
    def list_receptacles(self):
        """
        :return: list of probe drive receptacle numbers
        :rtype: [int, ]
        """
        return list(self._configs)

    def _parse_motionlist(self, ml_gname):
        # A motion list group follows the naming scheme of:
        #    'Motion list: ml_name'
        #
        # initialize return values
        is_ml = False
        ml_name = None
        ml_config = None

        # Determine if ml_group is a motion list
        if 'Motion list' == ml_gname.split(': ')[0]:
            is_ml = True
            ml_name = ml_gname.split(': ')[-1]

            ml_group = self.group[ml_gname]
            ml_config = {'delta': (ml_group.attrs['Delta x'],
                                   ml_group.attrs['Delta y'],
                                   0.0),
                         'center': (ml_group.attrs['Grid center x'],
                                    ml_group.attrs['Grid center y'],
                                    0.0),
                         'npoints': (ml_group.attrs['Nx'],
                                     ml_group.attrs['Ny'],
                                     1)}

        return is_ml, ml_name, ml_config

    def _parse_probelist(self, p_gname):
        # A probe list group follows the naming scheme of:
        #    'Probe: XY[#]: p_name'
        #
        # initialize return values
        is_p = False
        p_name = None
        p_config = None

        # Determine if p_group is a probe config
        if 'Probe' == p_gname.split(': ')[0]:
            is_p = True
            p_name = p_gname.split(': ')[-1]

            p_group = self.group[p_gname]
            p_config = {'receptacle': p_group.attrs['Receptacle'],
                        'port': p_group.attrs['Port']}

        return is_p, p_name, p_config
