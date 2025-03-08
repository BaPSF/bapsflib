import numpy as np
import unittest as ut

from abc import ABC
from enum import Enum

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib._hdf.maps.templates import HDFMapTemplate, MapTypes


class TestMapTypesEnum(ut.TestCase):
    def test_assert_enum(self):
        assert issubclass(MapTypes, Enum)

    def test_digitizer(self):
        assert hasattr(MapTypes, "DIGITIZER")

    def test_control(self):
        assert hasattr(MapTypes, "CONTROL")

    def test_msi(self):
        assert hasattr(MapTypes, "MSI")


class TestHDFMapTemplate(ut.TestCase):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName=methodName)

        # Create a fully defined DummyMap to test basic functionality
        # of HDFMapTemplate
        new__dict__ = HDFMapTemplate.__dict__.copy()
        for _abc_method_name in HDFMapTemplate.__abstractmethods__:
            new__dict__[_abc_method_name] = lambda *args, **kwargs: NotImplemented

        # Creates class DummyMap which is subclass of HDFMapTemplate with
        # all abstract methods returning NotImplemented
        self._DummyMap = type("DummyMap", (HDFMapTemplate,), new__dict__)
        self._DummyMap._maptype = MapTypes.MSI

    def setUp(self):
        # blank/temporary HDF5 file
        self.f = FauxHDFBuilder()

        # add come contents to the MSI group
        self.f["MSI"].create_group("g1")
        self.f["MSI"].create_group("g2")

        dtype = np.dtype([("Shot number", np.int32), ("Value", np.int8)])
        data = np.empty((5,), dtype=dtype)
        self.f["MSI"].create_dataset("d1", data=data)

    def tearDown(self):
        """Cleanup temporary HDF5 file"""
        self.f.cleanup()

    def test_abstractness(self):
        assert issubclass(HDFMapTemplate, ABC)

    def test_attribute_existence(self):
        expected_attributes = {
            "_init_before_build_configs",
            "configs",
            "dataset_names",
            "group",
            "group_name",
            "group_path",
            "info",
            "maptype",
            "subgroup_names",
        }
        for attr_name in expected_attributes:
            with self.subTest(attr_name=attr_name):
                assert hasattr(HDFMapTemplate, attr_name)

    def test_abstractmethod_existence(self):
        assert "_build_configs" in HDFMapTemplate.__abstractmethods__

    def test_not_hdf5_group(self):
        with self.assertRaises(TypeError):
            self._DummyMap(None)

    def test_attribute_values(self):
        _map = self._DummyMap(self.f["MSI"])
        _expected = {
            "configs": dict(),
            "dataset_names": ["d1"],
            "group": self.f["MSI"],
            "group_name": "MSI",
            "group_path": "/MSI",
            "maptype": MapTypes.MSI,
            "subgroup_names": ["g1", "g2"],
        }
        for attr_name, expected in _expected.items():
            with self.subTest(attr_name=attr_name, expected=expected):
                self.assertEqual(getattr(_map, attr_name), expected)

    def test_info_dict(self):
        _map = self._DummyMap(self.f["MSI"])

        _expected = {
            True: isinstance(_map.info, dict),
            "group name": "MSI",
            "group path": "/MSI",
            "maptype": _map.maptype,
        }
        for key, expected in _expected.items():
            with self.subTest(key=key, expected=expected):
                val = key if not isinstance(key, str) else _map.info[key]
                self.assertEqual(val, expected)
