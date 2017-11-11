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

from .control_template import hdfMap_control_template


class hdfMap_control_6k(hdfMap_control_template):
    def __init__(self, control_group):
        hdfMap_control_template.__init__(self, control_group)

        # define control type
        self.info['contype'] = 'motion'

        # populate self.configs
        self._build_configs()

        # remove self.info and self.configs items that
        self._verify_map()

    def _build_configs(self):
        # remove 'config names'
        if 'config names' in self.configs:
            del self.configs['config names']

        # build 'motion list' and 'probe list'
        self.configs['motion list'] = []
        self.configs['probe list'] = []
        for name in self.sgroup_names:
            is_ml, ml_name, ml_config = self._parse_motionlist(name)
            if is_ml:
                # build 'motion list'
                self.configs['motion list'].append(ml_name)
                self.configs[ml_name] = ml_config
            else:
                is_p, p_name, p_config = self._parse_probelist(name)
                if is_p:
                    # build 'probe list'
                    self.configs['probe list'].append(p_name)
                    self.configs[p_name] = p_config

        # Define number of controlled probes
        self.configs['nControlled'] = len(self.configs['probe list'])

        # Define 'dataset fields'
        self.configs['dataset fields'] = [
            ('Shot number', '<u4'),
            ('x', '<f8'),
            ('y', '<f8'),
            ('z', '<f8'),
            ('theta', '<f8'),
            ('phi', '<f8')
        ]

        # Define 'dset field to numpy field'
        self.configs['dset field to numpy field'] = [
            ('Shot number', 'shotnum', 0),
            ('x', 'xyz', 0),
            ('y', 'xyz', 1),
            ('z', 'xyz', 2),
            ('theta', 'ptip_rot_theta', 0),
            ('phi', 'ptip_rot_phi', 0)
        ]

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
        for name in self.configs['probe list']:
            if self.configs[name]['receptacle'] == receptacle:
                pname = name

        # Construct dataset name
        dname = 'XY[{0}]: {1}'.format(receptacle, pname)

        return dname

    @property
    def list_receptacles(self):
        """
        :return: list of probe drive receptacle numbers
        :rtype: [int, ]
        """
        receptacles = []
        for name in self.configs['probe list']:
            receptacles.append(self.configs[name]['receptacle'])
        return receptacles

    @property
    def unique_specifiers(self):
        """
        :return: list of control device unique specifiers. Here the
            unique specifier is the probe drive receptacle number.
        :rtype: [int, ]
        """
        return self.list_receptacles

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
