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
    """Open a HDF5 file created by the LaPD at BaPSF."""

    def __init__(self, name: str, mode='r', silent=False, **kwargs):
        """
        :param name: name (and path) of file on disk
        :param mode: readonly :code:`'r'` (DEFAULT) and read/write
            :code:`'r+'`
        :param silent: set :code:`True` to suppress warnings
            (:code:`False` DEFAULT)
        :param kwargs: additional keywords passed on to
            :class:`h5py.File`
        """
        super().__init__(name, mode=mode,
                         control_path='Raw data + config',
                         digitizer_path='Raw data + config',
                         msi_path='MSI', silent=silent, **kwargs)

    def _map_file(self):
        """Map/re-map the LaPD HDF5 file."""
        self._file_map = LaPDMap(self, control_path=self.CONTROL_PATH,
                                 digitizer_path=self.DIGITIZER_PATH,
                                 msi_path=self.MSI_PATH)

    def _build_info(self):
        # run inherited code
        super()._build_info()

        # add 'lapd version' to `_info`
        self.info['lapd version'] = self.file_map.lapd_version

        # add run info
        self.info.update(self.file_map.run_info)

        # add experiment info
        self.info.update(self.file_map.exp_info)

    @property
    def file_map(self) -> LaPDMap:
        """LaPD HDF5 file map (:class:`~.lapdmap.LaPDMap`)"""
        return self._file_map

    def run_description(self):
        """Description of experimental run (from the HDF5 file)"""
        for line in self._info['run description'].splitlines():
            print(line)
