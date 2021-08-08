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


class FauxGasPressure(h5py.Group):
    """
    Creates a Faux 'Gas pressure' Group in the HDF5 file.
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
            """Reset 'Discharge' group to defaults."""
            self._faux._update()

    def __init__(self, id, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError(f"{id} is not a GroupID")

        # create control group
        # noinspection PyUnresolvedReferences
        gid = h5py.h5g.create(id, b"Gas pressure")
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

        # ------ build 'Gas pressure summary' dataset              -----
        dset_name = "Gas pressure summary"
        shape = (2,)
        dtype = np.dtype(
            [
                ("Shot number", np.int32),
                ("Timestamp", np.float64),
                ("Ion gauge data valid", np.int8),
                ("RGA data valid", np.int8),
                ("Fill pressure", np.float32),
                ("Peak AMU", np.float32),
            ]
        )
        data = np.empty(shape, dtype=dtype)
        data["Shot number"] = np.array([0, 19251])
        data["Timestamp"] = np.array([3.4658681569157567e9, 3.4658922665056167e9])
        data["Ion gauge data valid"] = np.array([0, 0])
        data["RGA data valid"] = np.array([0, 0])
        data["Fill pressure"] = np.array([4.2e-5, 4.2e-5])
        data["Peak AMU"] = np.array([2.0, 2.0])
        self.create_dataset(dset_name, data=data)

        # ------ build 'RGA partial pressures' dataset             -----
        dset_name = "RGA partial pressures"
        shape = (2, 50)
        data = np.zeros(shape, dtype=np.float32)
        self.create_dataset(dset_name, data=data)

    def _set_attrs(self):
        """Set the 'Gas pressure' group attributes"""
        # assign attributes
        self.attrs.update(
            {
                "Ion gauge calibration tag": b"03/01/2006",
                "RGA AMUs": np.arange(1, 51, 1, dtype=np.int32),
                "RGA calibration tag": b"03/01/2006",
            }
        )
