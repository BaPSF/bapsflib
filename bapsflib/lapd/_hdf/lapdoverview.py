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
"""
Module containing the LaPD overview class.
"""
__all__ = ["LaPDOverview"]

from bapsflib._hdf.utils.hdfoverview import HDFOverview
from bapsflib.lapd._hdf.file import File


class LaPDOverview(HDFOverview):
    """
    Reports an overview of the LaPD HDF5 file mapping.
    """

    def __init__(self, hdf_obj: File):
        """
        :param hdf_obj: HDF5 file object
        :type hdf_obj: :class:`~bapsflib.lapd._hdf.file.File`
        """
        super().__init__(hdf_obj)

    def report_general(self):
        """
        Prints general HDF5 file info.
        """
        super().report_general()

        # add more print basic file info
        print(
            f"LaPD version: {self._file.info['lapd version']}\n"
            f"Investigator: {self._file.info['investigator']}\n"
            f"Run Date:     {self._file.info['run date']}\n"
            f"\n"
            f"Exp. and Run Structure:\n"
            f"  (set)  {self._file.info['exp set name']}\n"
            f"  (exp)  +-- {self._file.info['exp name']}\n"
            f"  (run)  |   +-- {self._file.info['run name']}"
        )

        # print run description
        print("\nRun Description:")
        for line in self._file.info["run description"].splitlines():
            print(f"    {line}")

        # print exp description
        print("\nExp. Description:")
        for line in self._file.info["exp description"].splitlines():
            print(f"    {line}")
