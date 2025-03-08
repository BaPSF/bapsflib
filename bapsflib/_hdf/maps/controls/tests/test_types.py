import unittest as ut

from enum import Enum

from bapsflib._hdf.maps.controls.types import ConType


class TestConTypeEnum(ut.TestCase):
    def test_assert_enum(self):
        assert issubclass(ConType, Enum)

    def test_enum_instances(self):
        _types = {
            "MOTION",
            "POWER",
            "TIMING",
            "WAVEFORM",
        }
        for contype in _types:
            with self.subTest(contype=contype):
                self.assertTrue(hasattr(ConType, contype))

    def test__repr__(self):
        _types = {
            "MOTION",
            "POWER",
            "TIMING",
            "WAVEFORM",
        }
        for contype in _types:
            with self.subTest(contype=contype):
                self.assertEqual(
                    getattr(ConType, contype).__repr__(),
                    f"contype.{contype}",
                )
