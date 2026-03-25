import h5py
import numpy as np

from bapsflib._hdf.maps.controls.phys180e import HDFMapControlPositions180E
from bapsflib._hdf.maps.controls.tests.common import ControlTestCase
from bapsflib._hdf.maps.controls.tests.fauxpositions180e import FauxPositions180E
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib.utils.exceptions import HDFMappingError
from bapsflib.utils.warnings import HDFMappingWarning


class TestPositions180E(ControlTestCase):
    """Test class for HDFMapControlBMControl"""

    # define setup variables
    DEVICE_NAME = "180E_positions"
    DEVICE_PATH = "Raw data + config/Positions"
    MAP_CLASS = HDFMapControlPositions180E
    CONTYPE = ConType.MOTION

    @property
    def map(self) -> HDFMapControlPositions180E:
        return super().map

    @property
    def mod(self) -> FauxPositions180E:
        return super().mod

    def test_device_name(self):
        _map = self.map
        self.assertEqual(_map.device_name, "180E_positions")

    def test_group_name(self):
        _map = self.map
        self.assertEqual(_map.group_name, "Positions")

    def test_expected_group_name(self):
        _map = self.map
        self.assertEqual(_map._EXPECTED_GROUP_NAME, "Positions")

    def test_required_dataset_names(self):
        self.assertEqual(
            self.MAP_CLASS._required_dataset_names,
            {"main": "positions_setup_array"},
        )

    def test_raises_too_many_datasets(self):
        _group = self.dgroup  # type: h5py.Group
        _group.create_dataset("extra_dataset", data=np.linspace(0, 10, 1))
        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_raises_missing_required_dataset(self):
        for dset_name in self.MAP_CLASS._required_dataset_names.values():
            self.f.remove_all_modules()
            self.f.add_module(self.DEVICE_NAME)

            _group = self.dgroup  # type: h5py.Group
            del _group[dset_name]

            with self.subTest(name=dset_name), self.assertRaises(HDFMappingError):
                _map = self.map
