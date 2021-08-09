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

from warnings import warn


class FauxInterferometerArray(h5py.Group):
    """
    Creates a Faux 'Interferometer array' Group in a HDF5 file.
    """

    # noinspection PyProtectedMember
    class _knobs(object):
        """
        A class that contains all the controls (knobs) for specifying
        the MSI diagnostic group structure.
        """

        def __init__(self, val):
            super().__init__()
            self._faux = val

        @property
        def n_interferometers(self):
            """Number of Interferometers"""
            return self._faux._n_interferometers

        @n_interferometers.setter
        def n_interferometers(self, val):
            """Set the number of interferometers (1 to 7)"""
            if isinstance(val, int) and 1 <= val <= 7:
                if val != self._faux._n_interferometers:
                    self._faux._n_interferometers = val
                    self._faux._update()
            else:
                warn("`val` not valid, no update performed")

        def reset(self):
            """Reset 'Interferometer array' group to defaults."""
            self._faux._n_interferometers = 7
            self._faux._update()

    def __init__(self, id, n_interferometers=7, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError(f"{id} is not a GroupID")

        # create control group
        # noinspection PyUnresolvedReferences
        gid = h5py.h5g.create(id, b"Interferometer array")
        h5py.Group.__init__(self, gid)

        # define key values
        # - (1 <= n_interferometers <= 7)
        #
        if isinstance(n_interferometers, int) and 1 <= n_interferometers <= 7:
            self._n_interferometers = n_interferometers
        else:
            self._n_interferometers = 7

        # build MSI diagnostic sub-groups, datasets, and attributes
        self._update()

    @property
    def knobs(self):
        """
        Knobs for controlling structure of the MSI diagnostic
        group
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
        self._set_interarr_attrs()

        # build interferometer sub-groups
        for i in range(self._n_interferometers):
            self._build_interferometer_group(i)

    def _set_interarr_attrs(self):
        """Sets the 'Interferometer array' group attributes"""
        bar_arr = [7.9999999e13] + ([1.17000001e14] * 6)
        zloc = [958.5, 1501.65, 1214.1, 958.5, 670.95, 415.35, 127.8]
        self.attrs.update(
            {
                "Calibration tag": b"12/07/2009",
                "Interferometer count": self._n_interferometers,
                "Start times": [-0.0249846] * self._n_interferometers,
                "Timesteps": [4.88e-5] * self._n_interferometers,
                "n_bar_L": bar_arr[: self._n_interferometers :],
                "z locations": zloc[: self._n_interferometers :],
            }
        )

    def _build_interferometer_group(self, inter_num):
        """
        Builds interferometer group for interferometer
        :data:`inter_num`.

        :param int inter_num:  interferometer number (0 to 6)
        """
        # Order of operations
        # 1. create interferometer group
        # 2. define attributes for group
        # 3. create group's datasets
        #    - 'Interferometer trace' -- contains the interferometer
        #      signal for the first and last HDF5 shot numbers
        #    - 'Interferometer summary list' -- contains metadata
        #      associated with each interferometer trace
        #
        # Create group
        gname = f"Interferometer [{inter_num}]"
        self.create_group(gname)

        # Set group attributes
        self[gname].attrs.update(
            {
                "Start time": self.attrs["Start times"][inter_num],
                "Timestep": self.attrs["Timesteps"][inter_num],
                "n_bar_L": self.attrs["n_bar_L"][inter_num],
                "z location": self.attrs["z locations"][inter_num],
            }
        )

        # Create datasets
        self._build_interferometer_datasets(gname)

    def _build_interferometer_datasets(self, inter_gname):
        """
        Builds the datasets for interferometer associated with
        :data:`inter_gname`.

        :param str inter_gname: name of interferometer group
        """
        # ------ Build trace dataset                              ------
        dname = "Interferometer trace"
        shape = (2, 100)
        data = np.zeros(shape, dtype=np.float32)
        self[inter_gname].create_dataset(dname, data=data)

        # ------ Build summary dataset                            ------
        dname = "Interferometer summary list"
        shape = (2,)
        dtype = np.dtype(
            [
                ("Shot number", np.int32),
                ("Timestamp", np.float64),
                ("Data valid", np.int8),
                ("Peak density", np.float32),
            ]
        )
        data = np.empty(shape, dtype=dtype)
        data["Shot number"] = np.array([0, 19251])
        data["Timestamp"] = np.array([3.4658681569157567e9, 3.4658922665056167e9])
        data["Data valid"] = np.array([0, 0])
        data["Peak density"] = np.array([6.542343e12, 6.4398804e12])
        self[inter_gname].create_dataset(dname, data=data)
