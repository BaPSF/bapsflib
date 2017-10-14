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

        # build self.configs
        self._build_config()

        # remove self.info and self.config items that
        self._verify_map()

    def _build_config(self):
        # remove 'command list'
        if 'command list' in self.config:
            del(self.config['command list'])

        # build 'motion list' and 'probe list'
        self.config['motion list'] = []
        self.config['probe list'] = []
        for name in self.sgroup_names:
            is_ml, ml_name, ml_config = self._parse_motionlist(name)
            if is_ml:
                # build 'motion list'
                self.config['motion list'].append(ml_name)
                self.config[ml_name] = ml_config
            else:
                is_p, p_name, p_config = self._parse_probelist(name)
                if is_p:
                    # build 'probe list'
                    self.config['probe list'].append(p_name)
                    self.config[p_name] = p_config

        # Define number of controlled probes
        self.config['nControlled'] = len(self.config['probe list'])

        # Define 'dataset fields'
        self.config['dataset fields'] = [
            ('Shot number', '<u4'),
            ('x', '<f8'),
            ('y', '<f8'),
            ('z', '<f8'),
            ('theta', '<f8'),
            ('phi', '<f8')
        ]

        # Define 'dset field to numpy field'
        self.config['dset field to numpy field'] = [
            ('Shot number', 'shotnum', 0),
            ('x', 'xyz', 0),
            ('y', 'xyz', 1),
            ('z', 'xyz', 2)
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
        for name in self.config['probe list']:
            if self.config[name]['receptacle'] == receptacle:
                pname = name

        # Construct dataset name
        dname = 'XY[{0}]: {1}'.format(receptacle, pname)

        return dname

    @property
    def list_receptacles(self):
        receptacles = []
        for name in self.config['probe list']:
            receptacles.append(self.config[name]['receptacle'])
        return receptacles

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

            ml_group = self.control_group[ml_gname]
            ml_config = {'delta': (ml_group.attrs['Delta x'],
                                   ml_group.attrs['Delta y'],
                                   0.0),
                         'center': (ml_group.attrs['Grid center x'],
                                    ml_group.attrs['Grid center y'],
                                    0.0),
                         'npoints': (ml_group.attrs['Nx'],
                                     ml_group.attrs['Ny'],
                                     0)}

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

            p_group = self.control_group[p_gname]
            p_config = {'receptacle': p_group.attrs['Receptacle'],
                        'port': p_group.attrs['Port']}

        return is_p, p_name, p_config
