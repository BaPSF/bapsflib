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
from bapsflib._hdf import File as BaseFile
from .lapdmap import LaPDMap


class File(BaseFile):

    def __init__(self, name, mode='r', **kwargs):
        super().__init__(name, mode=mode, **kwargs)

    def _map_file(self):
        self._file_map = LaPDMap(self)

    def _build_info(self):
        # run inherited code
        super()._build_info()

        # add 'lapd version' to `_info`
        self._info['lapd version'] = self.file_map.lapd_version
