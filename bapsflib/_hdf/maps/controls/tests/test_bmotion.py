import unittest as ut

from bapsflib._hdf.maps.controls.bmotion import HDFMapControlBMotion
from bapsflib._hdf.maps.controls.tests.common import ControlTestCase
from bapsflib._hdf.maps.controls.types import ConType


class TestBMotion(ControlTestCase):
    """Test class for HDFMapControlBMControl"""

    # define setup variables
    DEVICE_NAME = "bmotion"
    DEVICE_PATH = "Raw data + config/bmotion"
    MAP_CLASS = HDFMapControlBMotion
    CONTYPE = ConType.MOTION

    def test_raises(self):
        ...

    @ut.skip("Not implemented")
    def test_warnings(self):
        ...

    def test_generate_config_name(self):
        _map = self.MAP_CLASS
        _conditions = [
            # (args, expected)
            ((5, "my_motion_group"), "5 - my_motion_group"),
            ((20, "foo"), "20 - foo"),
            (("5", "<Hades>    n21x21"), "5 - <Hades>    n21x21"),
        ]
        for args, expected in _conditions:
            with self.subTest(args=args, expected=expected):
                self.assertEqual(_map._generate_config_name(*args), expected)

    def test_split_config_name(self):
        _map = self.MAP_CLASS
        _conditions = [
            # (assert_type, args, expected)
            ("equal", ("5 - my_motion_group",), ("5", "my_motion_group")),
            ("equal", ("20 - foo",), ("20", "foo")),
            ("equal", ("20 - <Hades>    n21x21",), ("20", "<Hades>    n21x21")),
            ("is", ("five",), None),
            ("is", ("A - my_motion_group",), None),
            ("is", ("5 ~ my_motion_group",), None),
        ]
        for assert_type, args, expected in _conditions:
            with self.subTest(assert_type=assert_type, args=args, expected=expected):
                if assert_type == "equal":
                    self.assertEqual(_map._split_config_name(*args), expected)
                elif assert_type == "is":
                    self.assertIs(_map._split_config_name(*args), expected)
                else:
                    self.fail(f"Test assert_type '{assert_type}' is unknown.")
