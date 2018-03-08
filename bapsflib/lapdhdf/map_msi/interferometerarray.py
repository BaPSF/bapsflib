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
import h5py

from .msi_template import hdfMap_msi_template


# noinspection PyPep8Naming
class hdfMap_msi_interarr(hdfMap_msi_template):
    """
    Mapping class for the 'Interferometer array' MSI diagnostic.
    """
    def __init__(self, diag_group):
        """
        :param diag_group: the HDF5 MSI diagnostic group
        :type diag_group: :class:`h5py.Group`
        """
        # initialize
        hdfMap_msi_template.__init__(self, diag_group)

        # populate self.configs
        self._build_configs()

    def _build_configs(self):
        pass
