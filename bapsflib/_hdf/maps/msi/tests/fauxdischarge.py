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


class FauxDischarge(h5py.Group):
    """
    Creates a Faux 'Discharge' Group in the HDF5 file.
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
        gid = h5py.h5g.create(id, b"Discharge")
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

        # define a time array for dataset population
        tarr = np.linspace(
            0, 2048 * self.attrs["Timestep"], num=2048, endpoint=False, dtype=np.float32
        )

        # ------ build 'Cathode-anode voltage' dataset             -----
        dset_name = "Cathode-anode voltage"
        shape = (2, 2048)
        data = np.empty(shape, dtype=np.float32)
        data[0] = np.sin(2.0 * np.pi * tarr)
        data[1] = data[0] - (0.2 * np.pi)
        self.create_dataset(dset_name, data=data)

        # ------ build 'Discharge current' dataset                 -----
        dset_name = "Discharge current"
        shape = (2, 2048)
        data = np.empty(shape, dtype=np.float32)
        data[0] = np.cos(2.0 * np.pi * tarr)
        data[1] = data[0] - (0.2 * np.pi)
        self.create_dataset(dset_name, data=data)

        # ------ build 'Discharge summary' dataset                 -----
        dset_name = "Discharge summary"
        shape = (2,)
        dtype = np.dtype(
            [
                ("Shot number", np.int32),
                ("Timestamp", np.float64),
                ("Data valid", np.int8),
                ("Pulse length", np.float32),
                ("Peak current", np.float32),
                ("Bank voltage", np.float32),
            ]
        )
        data = np.empty(shape, dtype=dtype)
        data["Shot number"] = np.array([0, 19251])
        data["Timestamp"] = np.array([3.4658681569157567e9, 3.4658922665056167e9])
        data["Data valid"] = np.array([0, 0])
        data["Pulse length"] = np.array([0.0, 0.0])
        data["Peak current"] = np.array([6127.1323, 6050.814])
        data["Bank voltage"] = np.array([66.7572, 66.45203])
        self.create_dataset(dset_name, data=data)

    def _set_attrs(self):
        """Set the 'Discharge' group attributes"""
        # assign attributes
        self.attrs.update(
            {
                "Calibration tag": np.bytes_(""),
                "Current conversion factor": np.float32(0.0),
                "Start time": np.float32(-0.0249856),
                "Timestep": np.float32(4.88e-5),
                "Voltage conversion factor": np.float32(0.0),
            }
        )
