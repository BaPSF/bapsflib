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


class hdfMap_control_waveform(hdfMap_control_template):
    def __init__(self, control_group):
        hdfMap_control_template.__init__(self, control_group)

        # define control type
        self.info['contype'] = 'waveform'

        # build self.config
        self._build_config()

        # verify self.info and self.config
        self._verify_map()

    def _build_config(self):
        pass
