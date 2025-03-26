import numpy as np
import unittest as ut

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib._hdf.maps.msi.templates import HDFMapMSITemplate
from bapsflib._hdf.maps.templates import HDFMapTemplate, MapTypes


class TestHDFMapMSITemplate(ut.TestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName=methodName)

        # Create a fully defined DummyMap to test basic functionality
        # of HDFMapTemplate
        new__dict__ = HDFMapMSITemplate.__dict__.copy()
        for _abc_method_name in HDFMapMSITemplate.__abstractmethods__:
            new__dict__[_abc_method_name] = lambda *args, **kwargs: NotImplemented

        # Creates class DummyMap which is subclass of HDFMapTemplate with
        # all abstract methods returning NotImplemented
        self._DummyMap = type("DummyMap", (HDFMapMSITemplate,), new__dict__)

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

    def test_inheritance(self):
        self.assertTrue(issubclass(HDFMapMSITemplate, HDFMapTemplate))

    def test_maptype(self):
        self.assertEqual(HDFMapMSITemplate._maptype, MapTypes.MSI)

    def test_attribute_values(self):
        _map = self._DummyMap(self.f["MSI"])
        _expected = {
            "configs": dict(),
            "group_name": "MSI",
            "device_name": _map.group_name,
            "maptype": MapTypes.MSI,
        }
        for attr_name, expected in _expected.items():
            with self.subTest(attr_name=attr_name, expected=expected):
                self.assertEqual(getattr(_map, attr_name), expected)
