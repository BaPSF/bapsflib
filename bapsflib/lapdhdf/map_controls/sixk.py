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

        # Define 'data fields'
        self.config['data fields'] = [
            ('Shot number', '<u4'),
            ('x', '<f8'),
            ('y', '<f8'),
            ('z', '<f8'),
            ('theta', '<f8'),
            ('phi', '<f8')
        ]

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
