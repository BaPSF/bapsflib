import h5py
import numpy as np


class FauxPositions180E(h5py.Group):
    """
    Creates a Faux `180E_Positions` control group in the HDF5 file.
    """

    class Knobs:
        """
        A class that contains all the controls for specifying the
        control device group structure.
        """

        def __init__(
            self,
            faux: "FauxPositions180E",
            sn_size: int,
        ):
            self._faux = faux

            # initialize knobs
            self._pause_populate = True
            self._sn_size = None
            self.sn_size = sn_size
            self._pause_populate = False

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

            # update
            self._sn_size = val
            self._faux.populate(skip_populate=self._pause_populate)

        def reset(self):
            """Reset to defaults"""
            self._sn_size = 100
            self._faux.populate()

    def __init__(
        self,
        id: h5py.h5g.GroupID,
        sn_size: int = 100,
    ):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError(f"{id} is not a GroupID")

        # create control group
        gid = h5py.h5g.create(id, b"Positions")
        super().__init__(gid)

        # store number on configurations
        self._knobs = self.Knobs(self, sn_size)

        # initialize some attributes
        self._shotnum = None

        # build control device sub-groups, datasets, and attributes
        self.populate()

    @property
    def knobs(self) -> Knobs:
        return self._knobs

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

    def _add_positions_dataset(self):
        dset_name = "positions_setup_array"
        shape = (self.knobs.sn_size,)
        dtype = np.dtype(
            [
                ("Line_number", np.uint32),
                ("x", np.float32),
                ("y", np.float32),
            ]
        )
        data = np.empty(shape, dtype=dtype)

        self._shotnum = np.arange(1, self.knobs.sn_size + 1, dtype=np.uint32)
        motion_list = self.motionlist

        data["Line_number"][...] = self._shotnum
        data["x"][...] = motion_list[..., 0]
        data["y"][...] = motion_list[..., 1]

        self.create_dataset(dset_name, data=data)

    def populate(self, skip_populate=False):
        if skip_populate:
            return

        # clear group and re-initialize before rebuild
        self.clear()
        self._shotnum = None

        # add datasets
        self._add_positions_dataset()
