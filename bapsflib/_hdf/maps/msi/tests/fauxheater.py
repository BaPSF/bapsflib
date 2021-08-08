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


class FauxHeater(h5py.Group):
    """
    Creates a Faux 'Heater' Group in the HDF5 file.
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
        gid = h5py.h5g.create(id, b"Heater")
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

        # ------ build 'Heater summary' dataset                    -----
        dset_name = "Heater summary"
        shape = (2,)
        dtype = np.dtype(
            [
                ("Shot number", np.int32),
                ("Timestamp", np.float64),
                ("Data valid", np.int8),
                ("Heater current", np.float32),
                ("Heater voltage", np.float32),
                ("Heater temperature", np.float32),
            ]
        )
        data = np.empty(shape, dtype=dtype)
        data["Shot number"] = np.array([0, 19251])
        data["Timestamp"] = np.array([3.4658681569157567e9, 3.4658922665056167e9])
        data["Data valid"] = np.array([0, 0])
        data["Heater current"] = np.array([1205.4824, 1240.1436])
        data["Heater voltage"] = np.array([23.004324, 22.7584])
        data["Heater temperature"] = np.array([818.6807, 817.3928])
        self.create_dataset(dset_name, data=data)

    def _set_attrs(self):
        """Set the 'Heater' group attributes"""
        # assign attributes
        self.attrs.update(
            {
                "Calibration tag": b"03/01/2006\n" b"but varies from cathode to cathode",
            }
        )
