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
import re

from .control_template import hdfMap_control_template


class hdfMap_control_waveform(hdfMap_control_template):
    def __init__(self, control_group):
        hdfMap_control_template.__init__(self, control_group)

        # define control type
        self.info['contype'] = 'waveform'

        # build self.config
        self._build_config()

        # verify self.info and self.config
        #self._verify_map()

    def _build_config(self):
        # remove 'motion list' and 'probe list' from self.config
        # - these are not used by this control device type
        #
        if 'motion list' in self.config:
            del self.config['motion list']
        if 'porbe list' in self.config:
            del self.config['probe list']

        # build 'config names'
        # - assume all subgroups are control device configuration groups
        #   and their names correspond to the configuration name
        #
        self.config['config names'] = self.sgroup_names

        # add 'config names' specific config info
        # - i.e. 'IP address' and 'command list'
        #
        for name in self.config['config names']:
            # get configuration group
            cgroup = self.control_group[name]

            # get IP address
            # - ip gets returned as a np.bytes_ string
            #
            ip = cgroup.attrs['IP address']
            ip = ip.decode('utf-8')

            # get command list
            # - cl gets returned as a np.bytes_ string
            #
            cl = cgroup.attrs['Waveform command list']
            cl = cl.decode('utf-8').splitlines()
            pattern = re.compile('(FREQ\s)(\d+\.\d+)')
            cl_float = []
            for val in cl:
                cl_re = re.search(pattern, val)
                cl_float.append(float(cl_re.group(2)))

            # assign values
            self.config[name] = {
                'IP address': ip,
                'command list': tuple(cl_float)
            }

            # define number of controlled probes
            self.config['nControlled'] = \
                len(self.config['config names'])

            # define 'dataset fields'
            self.config['dataset fields'] = [
                ('Shot number', '<u4'),
                ('Command index', '<u4')
            ]

            # define 'dset field to numpy field'
            self.config['dset field to numpy field'] = [
                ('Shot number', 'shotnum', 0),
                ('Command index', 'confreq', 0)
            ]

    @property
    def construct_dataset_name(self, *args):
        return 'Run time list'

    @property
    def unique_specifiers(self):
        return None
