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


class FauxSIS3301(h5py.Group):
    """
    Creates a Faux 'SIS 3301' Group in a HDF5 file.
    """

    def __init__(self, id, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError('{} is not a GroupID'.format(id))

        # create control group
        gid = h5py.h5g.create(id, b'SIS 3301')
        h5py.Group.__init__(self, gid)
