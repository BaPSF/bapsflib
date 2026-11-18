import h5py
import numpy as np

from typing import Tuple


class FauxLeCroy180E(h5py.Group):
    """
    Creates a Faux 'LeCroy_scope' Group in a HDF5 file.
    """

    # noinspection SpellCheckingInspection,PyProtectedMember
    class Knobs(object):
        """
        A class that contains all the controls for specifying the
        digitizer group structure.
        """

        def __init__(
            self,
            faux: "FauxLeCroy180E",
            sn_size: int,
            nt: int,
            active_channels: Tuple[int] | None,
        ):
            self._faux = faux
            self._sn_size = None
            self._nt = None
            self._active_channels = None

            self._pause_populate = True
            self.sn_size = sn_size
            self.nt = nt
            self.active_channels = active_channels
            self._pause_populate = False

        @property
        def sn_size(self) -> int:
            return self._sn_size

        @sn_size.setter
        def sn_size(self, val: int):
            if not isinstance(val, int) or val <= 0:
                return
            self._sn_size = val
            self._faux.populate(skip_populate=self._pause_populate)

        @property
        def nt(self) -> int:
            return self._nt

        @nt.setter
        def nt(self, val: int):
            if not isinstance(val, int) or val <= 0:
                return

            self._nt = val
            self._faux.populate(skip_populate=self._pause_populate)

        @property
        def active_channels(self) -> Tuple[int] | None:
            return self._active_channels

        @active_channels.setter
        def active_channels(self, val: Tuple[int] | None):
            if val is None:
                self._active_channels = None
                self._faux.populate(skip_populate=self._pause_populate)

            if (
                not isinstance(val, (tuple, list))
                or not all(isinstance(ch, int) for ch in val)
                or not all(ch in range(1, 5) for ch in val)
            ):
                return

            self._active_channels = val
            self._faux.populate(skip_populate=self._pause_populate)

    def __init__(
        self,
        id: h5py.Group,
        sn_size: int = 100,
        nt: int = 1000,
        active_channels: Tuple[int] | None = (1, 2),
    ):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError(f"{id} is not a GroupID")

        # create control group
        # noinspection PyUnresolvedReferences
        gid = h5py.h5g.create(id, b"LeCroy_scope")
        h5py.Group.__init__(self, gid)

        # initialize some attributes
        self._dt = 10.0e-9  # 10 ns
        self._channel_labels = ("Bx", "By", "Bz", "Isat")
        self._shotnum = None
        self._time = None
        self._configs = {}  # configurations dictionary

        # store number on configurations
        self._knobs = self.Knobs(
            self,
            sn_size=sn_size,
            nt=nt,
            active_channels=active_channels,
        )

        # build digitizer device sub-groups, datasets, and attributes
        self.populate()

    @property
    def knobs(self) -> Knobs:
        return self._knobs

    @property
    def configs(self) -> dict:
        return self._configs

    @property
    def dt(self) -> float:
        return self._dt

    def _add_channel_datasets(self):
        active_channels = self.knobs.active_channels

        if active_channels is None:
            return

        self._shotnum = np.arange(1, self.knobs.sn_size + 1, dtype=np.uint32)

        for ch in active_channels:
            dset_name = f"Channel{ch}"
            trace = 2.0 * np.sin(2 * np.pi * 10.0e6 * self._time)
            data = np.repeat(trace[None, ...], self.knobs.sn_size, axis=0)

            dset = self.create_dataset(dset_name, data=data)

            dset.attrs["description"] = self._channel_labels[ch - 1]
            dset.attrs["recorded"] = np.True_

    def _add_header_datasets(self):
        if "Headers" not in self:
            self.create_group("Headers")
        header_group = self["Headers"]

        if self.knobs.active_channels is None:
            return

        for ch in self.knobs.active_channels:
            dset_name = f"Channel{ch}"
            payload = np.void(
                b"\x57\x41\x56\x45\x44\x45\x53\x43\x00\x00\x00\x00\x00\x00\x00\x00\x4c"
                b"\x45\x43\x52\x4f\x59\x5f\x32\x5f\x33\x00\x00\x00\x00\x00\x00\x01\x00"
                b"\x01\x00\x5a\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x0d\x03\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x4c\x45\x43\x52\x4f\x59\x57\x53\x34"
                b"\x34\x58\x73\x00\x00\x00\x00\x17\x2d\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xa1\x86\x01\x00\xa0\x86\x01"
                b"\x00\xa0\x86\x01\x00\x00\x00\x00\x00\xa0\x86\x01\x00\x01\x00\x00\x00"
                b"\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x0a\x00\x00\x00\x00"
                b"\x00\x00\x00\xad\xdd\x26\x35\xad\xdd\x26\x35\x00\x5e\xf9\x46\x00\x5a"
                b"\xfb\xc6\x0a\x00\x01\x00\x95\xbf\x56\x34\x7b\x14\xae\x47\xe1\x7a\x84"
                b"\xbf\x7b\x14\xae\x47\xe1\x7a\x84\xbf\x56\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x53\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\xcc\xbc\x8c\x2b\xa6\x3b\xea\x10\x01\x29\x30\x40\x2b\x09"
                b"\x06\x0c\xe9\x07\x00\x00\x13\x60\x66\x3f\x00\x00\x00\x00\x00\x00\x01"
                b"\x00\x1c\x00\x02\x00\x00\x00\x80\x3f\x0b\x00\x01\x00\x00\x00\x80\x3f"
                b"\x00\x00\x00\x00\x03\x00"
            )  # this byte string is pulled directly from a sample HDF5 file
            trace = np.array([payload])
            data = np.repeat(trace[None, ...], self.knobs.sn_size, axis=0).squeeze()

            header_group.create_dataset(dset_name, data=data)

    def _add_time_dataset(self):
        dset_name = "time"
        self._time = self.dt * np.arange(0, self.knobs.nt, dtype=np.float32)
        self.create_dataset(dset_name, data=self._time)

    def _add_setup_array_dataset(self):
        dset_name = "LeCroy_scope_Setup_Arrray"
        data = np.array(b"Sorry, this is not included")
        self.create_dataset(dset_name, data=data)

    def populate(self, skip_populate=False):
        if skip_populate:
            return

        # clear group and re-initialize before rebuild
        self.clear()
        self.configs.clear()
        self._shotnum = None
        self._time = None

        # add datasets
        self._add_time_dataset()
        self._add_setup_array_dataset()
        self._add_channel_datasets()
        self._add_header_datasets()
