import unittest as ut

from enum import Enum

from bapsflib._hdf.maps.templates import MapTypes


class TestMapTypesEnum(ut.TestCase):
    def test_assert_enum(self):
        assert issubclass(MapTypes, Enum)

    def test_digitizer(self):
        assert hasattr(MapTypes, "DIGITIZER")

    def test_control(self):
        assert hasattr(MapTypes, "CONTROL")

    def test_msi(self):
        assert hasattr(MapTypes, "MSI")
