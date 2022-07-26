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
"""Module containing the HDF5 reader for LaPD generated files."""
__all__ = ["File"]

import h5py

from bapsflib._hdf.utils.file import File as BaseFile
from bapsflib.lapd._hdf.lapdmap import LaPDMap


class File(BaseFile):
    """Open a HDF5 file created by the LaPD at BaPSF."""

    def __init__(self, name: str, mode="r", silent=False, **kwargs):
        """
        :param name: name (and path) of file on disk
        :param mode: readonly :code:`'r'` (DEFAULT) and read/write
            :code:`'r+'`
        :param silent: set :code:`True` to suppress warnings
            (:code:`False` DEFAULT)
        :param kwargs: additional keywords passed on to
            :class:`h5py.File`

        :Example:

            >>> # open HDF5 file
            >>> f = File('sample.hdf5')
            >>> type(f)
            bapsflib.lapd._hdf.file.File
            >>> isinstance(f, bapsflib._hdf.utils.file.File)
            True
            >>> isinstance(f, h5py.File)
            True
        """
        super().__init__(
            name,
            mode=mode,
            control_path="Raw data + config",
            digitizer_path="Raw data + config",
            msi_path="MSI",
            silent=silent,
            **kwargs
        )

    def _build_info(self):
        """Builds the general :attr:`info` dictionary for the file."""
        # run inherited code
        super()._build_info()

        # add 'lapd version' to `_info`
        self.info["lapd version"] = self.file_map.lapd_version

        # add run info
        self.info.update(self.file_map.run_info)

        # add experiment info
        self.info.update(self.file_map.exp_info)

    def _map_file(self):
        """Map/re-map the LaPD HDF5 file. (Builds :attr:`file_map`)"""
        self._file_map = LaPDMap(
            self,
            control_path=self.CONTROL_PATH,
            digitizer_path=self.DIGITIZER_PATH,
            msi_path=self.MSI_PATH,
        )

    @property
    def file_map(self) -> LaPDMap:
        """LaPD HDF5 file map (:class:`~.lapdmap.LaPDMap`)"""
        return self._file_map

    @property
    def overview(self):
        """
        LaPD HDF5 file overview. (:class:`~.lapdoverview.LaPDOverview`)
        """
        # to avoid cyclical imports
        from bapsflib.lapd._hdf.lapdoverview import LaPDOverview

        return LaPDOverview(self)

    def run_description(self):
        """Print description of the LaPD experimental run."""
        for line in self.info["run description"].splitlines():
            print(line)
