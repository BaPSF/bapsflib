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
import numpy as np


class FauxMagneticField(h5py.Group):
    """
    Creates a Faux 'Magnetic field' Group in the HDF5 file.
    """

    class _knobs(object):
        """
        A class that contains all the controls (knobs) for specifying
        the MSI diagnostic group structure.
        """

        def __init__(self, val):
            super().__init__()
            self._faux = val

        def reset(self):
            """Reset 'Magnetic field' group to defaults."""
            self._faux._update()

    def __init__(self, id, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError(f"{id} is not a GroupID")

        # create control group
        # noinspection PyUnresolvedReferences
        gid = h5py.h5g.create(id, b"Magnetic field")
        h5py.Group.__init__(self, gid)

        # define key values

        # build MSI diagnostic sub-groups, datasets, and attributes
        self._update()

    @property
    def knobs(self):
        """
        Knobs for controlling structure of the MSI diagnostic group
        """
        return self._knobs(self)

    def _update(self):
        """
        Updates MSI diagnostic group structure (Groups, Datasets, and
        Attributes)
        """
        # clear group before rebuild
        self.clear()

        # set root attributes
        self._set_attrs()

        # ------ build 'Magnetic power supply currents' dataset    -----
        dset_name = "Magnet power supply currents"
        shape = (2, 10)
        data = np.zeros(shape, dtype=np.float32)
        self.create_dataset(dset_name, data=data)

        # ------ build 'Magnetic field profile' dataset            -----
        dset_name = "Magnetic field profile"
        shape = (2, 1024)
        data = np.zeros(shape, dtype=np.float32)
        self.create_dataset(dset_name, data=data)

        # ------ build 'Magnetic field summary' dataset            -----
        dset_name = "Magnetic field summary"
        shape = (2,)
        dtype = np.dtype(
            [
                ("Shot number", np.int32),
                ("Timestamp", np.float64),
                ("Data valid", np.int8),
                ("Peak magnetic field", np.float32),
            ]
        )
        data = np.empty(shape, dtype=dtype)
        data["Shot number"] = np.array([0, 19251])
        data["Timestamp"] = np.array([3.4658681569157567e9, 3.4658922665056167e9])
        data["Data valid"] = np.array([1, 1])
        data["Peak magnetic field"] = np.array([1092.8969, 1092.8975])
        self.create_dataset(dset_name, data=data)

    def _set_attrs(self):
        """Set the 'Magnetic field' group attributes"""
        # generate z locations
        zlocs = np.arange(0, 1024, 1, dtype=np.float32)
        zlocs = -300.0 + (zlocs * (2325.3 / 1023.0))

        # assign attributes
        self.attrs.update(
            {"Calibration tag": b"08/27/2013", "Profile z locations": zlocs}
        )
