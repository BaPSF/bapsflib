import h5py
import numpy as np
import textwrap

from datetime import datetime, timezone
from typing import Union


class FauxBMotion(h5py.Group):
    """
    Creates a Faux `bmotion` control group in the HDF5 file.
    """

    class Knobs:
        """
        A class that contains all the controls for specifying the
        control device group structure.
        """

        def __init__(self, faux: "FauxBMotion", n_motion_groups: int, sn_size: int):
            self._faux = faux

            # initialize knobs
            self._n_motion_groups = None
            self.n_motion_groups = n_motion_groups

            self._sn_size = None
            self.sn_size = sn_size

        @property
        def n_motion_groups(self):
            """Shot number size"""
            return self._n_motion_groups

        @n_motion_groups.setter
        def n_motion_groups(self, val: int):
            """Set shot number size"""
            # condition val
            if not isinstance(val, int) and not (
                isinstance(val, np.generic) and np.issubdtype(val, np.integer)
            ):
                raise TypeError(f"Expected type int, but got {type(val)}.")
            elif val < 1:
                raise ValueError(f"Given argument `val` ({val}) needs to >=1.")

            # only update if self._sn_size had been defined once prior
            if self._n_motion_groups is None:
                self._n_motion_groups = val
            else:
                self._n_motion_groups = val
                self._faux.populate()

        @property
        def sn_size(self):
            """Shot number size"""
            return self._sn_size

        @sn_size.setter
        def sn_size(self, val: int):
            """Set shot number size"""
            # condition val
            if not isinstance(val, int) and not (
                isinstance(val, np.generic) and np.issubdtype(val, np.integer)
            ):
                raise TypeError(f"Expected type int, but got {type(val)}.")
            elif val < 1:
                raise ValueError(f"Given argument `val` ({val}) needs to >=1.")

            # only update if self._sn_size had been defined once prior
            if self._sn_size is None:
                self._sn_size = val
            else:
                self._sn_size = val
                self._faux.populate()

        def reset(self):
            """Reset to defaults"""
            self._n_motion_groups = 1
            self._sn_size = 100
            self._faux.populate()

    def __init__(
        self,
        id: h5py.h5g.GroupID,
        n_motion_groups: int = 1,
        sn_size: int = 100,
    ):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError(f"{id} is not a GroupID")

        # create control group
        gid = h5py.h5g.create(id, b"bmotion")
        super().__init__(gid)

        # store number on configurations
        self._knobs = self.Knobs(self, n_motion_groups, sn_size)

        # initialize some attributes
        # self._n_motion_groups = 1
        # self._ml = []  # list of motion lists
        self._shotnum = None
        self.configs = {}  # configurations dictionary
        #
        # # set root attributes
        # self._set_xyz_attrs()
        #
        # build control device sub-groups, datasets, and attributes
        self.populate()

    @property
    def knobs(self) -> Knobs:
        return self._knobs

    @property
    def run_configuration_name(self):
        return "run_config_name"

    @property
    def shotnum(self):
        _size = self.knobs.sn_size
        self._shotnum = np.arange(1, _size + 1, 1, dtype=np.int32)
        return self._shotnum

    @property
    def motion_group_ids(self):
        return [f"{_id}" for _id in range(self.knobs.n_motion_groups)]

    @property
    def motion_group_names(self):
        return [f"mg{_id}" for _id in range(self.knobs.n_motion_groups)]

    @property
    def motionlist(self):
        shape = self.find_nearest_divisor(self.knobs.sn_size)
        if shape[0] * shape[1] != self.knobs.sn_size:
            shape = (self.knobs.sn_size, 1)

        motionlist = np.empty(shape + (2,), dtype=np.float32)
        motionlist[..., 0] = np.repeat(
            np.arange(0, shape[0], 1, dtype=np.float32)[..., None],
            shape[1],
            axis=1,
        )
        motionlist[..., 1] = np.repeat(
            np.arange(0, shape[1], 1, dtype=np.float32)[None, ...],
            shape[0],
            axis=0,
        )
        return np.reshape(motionlist, (self.knobs.sn_size, 2))

    @staticmethod
    def find_nearest_divisor(sn_size):
        closest_pair = (1, sn_size)
        sqrt_guess = np.int32(np.round(np.sqrt(sn_size)))
        for i in range(sqrt_guess, 0, -1):
            if sn_size % i == 0:
                if np.abs(i - (sn_size / i)) < np.abs(closest_pair[0] - closest_pair[1]):
                    closest_pair = (i, np.int32(sn_size / i))
        flip = True if np.random.randint(1, 100) <= 50 else False
        if flip:
            closest_pair = (closest_pair[1], closest_pair[0])

        return closest_pair

    def _add_dataset_run_time_list(self):
        dset_name = "Run time list"
        shape = (self.knobs.sn_size,)
        dtype = np.dtype(
            [
                ("Shot number", np.int32),
                ("Configuration name", np.bytes_, 120),
            ]
        )
        data = np.empty(shape, dtype=dtype)

        # populate dataset
        data["Shot number"][...] = self.shotnum[...]
        data["Configuration name"][...] = "run_config_name"

        # create dataset
        self.create_dataset(dset_name, data=data)

    def _add_dataset_bmotion_axis_names(self):
        dset_name = "bmotion_axis_names"
        shape = (self.knobs.sn_size * self.knobs.n_motion_groups,)
        dtype = np.dtype(
            [
                ("Shot number", np.int32),
                ("motion_group_id", np.bytes_, 120),
                ("motion_group_name", np.bytes_, 120),
                ("motionlist_index", np.int32),
                ("a0", np.bytes_, 120),
                ("a1", np.bytes_, 120),
                ("a2", np.bytes_, 120),
                ("a3", np.bytes_, 120),
                ("a4", np.bytes_, 120),
                ("a5", np.bytes_, 120),
            ]
        )
        data = np.empty(shape, dtype=dtype)

        # populate dataset
        data["Shot number"][...] = np.repeat(self.shotnum, self.knobs.n_motion_groups)
        data["motion_group_id"] = np.tile(
            np.array(self.motion_group_ids, dtype=(np.bytes_, 120)),
            self.knobs.sn_size,
        )
        data["motion_group_name"] = np.tile(
            np.array(self.motion_group_names, dtype=(np.bytes_, 120)),
            self.knobs.sn_size,
        )
        data["motionlist_index"] = np.repeat(self.shotnum - 1, self.knobs.n_motion_groups)
        data["a0"][...] = "X"
        data["a1"][...] = "Y"
        data["a2"][...] = ""
        data["a3"][...] = ""
        data["a4"][...] = ""
        data["a5"][...] = ""

        # create dataset
        self.create_dataset(dset_name, data=data)

    def _add_dataset_bmotion_positions(self):
        dset_name = "bmotion_positions"
        shape = (self.knobs.sn_size * self.knobs.n_motion_groups,)
        dtype = np.dtype(
            [
                ("Shot number", np.int32),
                ("motion_group_id", np.bytes_, 120),
                ("motion_group_name", np.bytes_, 120),
                ("motionlist_index", np.int32),
                ("a0", np.float64),
                ("a1", np.float64),
                ("a2", np.float64),
                ("a3", np.float64),
                ("a4", np.float64),
                ("a5", np.float64),
            ]
        )
        data = np.empty(shape, dtype=dtype)

        motionlist = self.motionlist

        # populate dataset
        data["Shot number"][...] = np.repeat(self.shotnum, self.knobs.n_motion_groups)
        data["motion_group_id"] = np.tile(
            np.array(self.motion_group_ids, dtype=(np.bytes_, 120)),
            self.knobs.sn_size,
        )
        data["motion_group_name"] = np.tile(
            np.array(self.motion_group_names, dtype=(np.bytes_, 120)),
            self.knobs.sn_size,
        )
        data["motionlist_index"] = np.repeat(self.shotnum - 1, self.knobs.n_motion_groups)
        data["a0"][...] = np.repeat(motionlist[..., 0], self.knobs.n_motion_groups)
        data["a1"][...] = np.repeat(motionlist[..., 1], self.knobs.n_motion_groups)
        data["a2"][...] = -9999
        data["a3"][...] = -9999
        data["a4"][...] = -9999
        data["a5"][...] = -9999

        # update configs
        for mg_name in self.motion_group_names:
            self.configs[mg_name]["state values"].update(
                {
                    "xyz": {
                        "dset paths": (f"{self.name}/bmotion_positions",),
                        "dset filed": ("a0", "a1", ""),
                        "shape": (3,),
                        "dtype": np.float64,
                        "config column": "motion_group_id",
                    },
                },
            )

        # create dataset
        self.create_dataset(dset_name, data=data)

    def _add_dataset_bmotion_target_positions(self):
        dset_name = "bmotion_target_positions"
        shape = (self.knobs.sn_size * self.knobs.n_motion_groups,)
        dtype = np.dtype(
            [
                ("Shot number", np.int32),
                ("motion_group_id", np.bytes_, 120),
                ("motion_group_name", np.bytes_, 120),
                ("motionlist_index", np.int32),
                ("a0", np.float64),
                ("a1", np.float64),
                ("a2", np.float64),
                ("a3", np.float64),
                ("a4", np.float64),
                ("a5", np.float64),
            ]
        )
        data = np.empty(shape, dtype=dtype)

        motionlist = self.motionlist

        # populate dataset
        data["Shot number"][...] = np.repeat(self.shotnum, self.knobs.n_motion_groups)
        data["motion_group_id"] = np.tile(
            np.array(self.motion_group_ids, dtype=(np.bytes_, 120)),
            self.knobs.sn_size,
        )
        data["motion_group_name"] = np.tile(
            np.array(self.motion_group_names, dtype=(np.bytes_, 120)),
            self.knobs.sn_size,
        )
        data["motionlist_index"] = np.repeat(self.shotnum - 1, self.knobs.n_motion_groups)
        data["a0"][...] = np.repeat(motionlist[..., 0], self.knobs.n_motion_groups)
        data["a1"][...] = np.repeat(motionlist[..., 1], self.knobs.n_motion_groups)
        data["a2"][...] = -9999
        data["a3"][...] = -9999
        data["a4"][...] = -9999
        data["a5"][...] = -9999

        # update configs
        for mg_name in self.motion_group_names:
            self.configs[mg_name]["state values"].update(
                {
                    "xyz": {
                        "dset paths": (f"{self.name}/bmotion_target_positions",),
                        "dset filed": ("a0", "a1", ""),
                        "shape": (3,),
                        "dtype": np.float64,
                        "config column": "motion_group_id",
                    },
                },
            )

        # create dataset
        self.create_dataset(dset_name, data=data)

    def _add_group_run_config(self):
        group_name = self.run_configuration_name
        self.create_group(group_name)
        group = self.get(group_name)

        group.attrs["BAPSFDAQ_MOTION_LV_VERSION"] = "2025.3.3"
        group.attrs["BAPSF_MOTION_VERSION"] = "0.2.8"
        group.attrs["EXPANSION_ATTR"] = ""

        slim_run_config = f"""
        [run]
        name = "{self.run_configuration_name}"
        date = "{datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        
        """
        for ii, mg_name in enumerate(self.motion_group_names):
            slim_run_config += f"""
            [run.motion_group.{ii}]
            name = "{mg_name}"
            drive.name = "drive{ii}"
            
            """

            self.configs[mg_name] = {
                "dset paths": (),
                "shotnum": {
                    "dset paths": None,
                    "dset field": ("Shot number",),
                    "shape": (),
                    "dtype": np.int32,
                },
                "state values": dict(),
            }

        group.attrs["RUN_CONFIG"] = textwrap.dedent(slim_run_config)

    def populate(self):
        """
        Updates the control group structure (Groups, Datasets, and
        Attributes)
        """
        # clear group before rebuild
        self.clear()

        # re-initialize key dicts
        self.configs.clear()

        # group needs to be added before datasets so self.config is
        # properly initialized
        self._add_group_run_config()

        # add datasets
        self._add_dataset_run_time_list()
        self._add_dataset_bmotion_axis_names()
        self._add_dataset_bmotion_positions()
        self._add_dataset_bmotion_target_positions()
