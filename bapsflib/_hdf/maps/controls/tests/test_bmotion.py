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

    def test_required_dataset_names(self):
        self.assertEqual(
            self.MAP_CLASS._required_dataset_names,
            {
                "main": "Run time list",
                "axis_names": "bmotion_axis_names",
                "positions": "bmotion_positions",
                "target_positions": "bmotion_target_positions",
            },
        )

    @ut.skip("Not implemented")
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

    def test_get_dataset(self):
        _map = self.map
        _group = self.dgroup

        _conditions = [
            # (assert_type, args, expected)
            ("equal", ("main",), _group["Run time list"]),
            ("equal", ("axis_names",), _group["bmotion_axis_names"]),
            ("equal", ("positions",), _group["bmotion_positions"]),
            ("equal", ("target_positions",), _group["bmotion_target_positions"]),
            ("raises", ("not_a_dataset",), ValueError),
        ]
        for assert_type, args, expected in _conditions:
            with self.subTest(assert_type=assert_type, args=args, expected=expected):
                if assert_type == "equal":
                    self.assertEqual(_map._get_dataset(*args), expected)
                elif assert_type == "raises":
                    with self.assertRaises(expected):
                        _map._get_dataset(*args)
                else:
                    self.fail(f"Test assert_type '{assert_type}' is unknown.")

    def test_construct_dataset_name(self):
        _map = self.map
        _conditions = [
            # (assert_type, args, expected)
            ("equal", ("main", ), "Run time list"),
            ("equal", ("axis_names",), "bmotion_axis_names"),
            ("equal", ("positions",), "bmotion_positions"),
            ("equal", ("target_positions",), "bmotion_target_positions"),
            ("raises", ("not_a_dataset",), ValueError),
        ]
        for assert_type, args, expected in _conditions:
            with self.subTest(assert_type=assert_type, args=args, expected=expected):
                if assert_type == "equal":
                    self.assertEqual(_map.construct_dataset_name(*args), expected)
                elif assert_type == "raises":
                    with self.assertRaises(expected):
                        _map.construct_dataset_name(*args)
                else:
                    self.fail(f"Test assert_type '{assert_type}' is unknown.")

    def test_get_config_id(self):
        _map = self.map
        _conditions = [
            # (assert_type, args, expected)
            ("equal", ("5 - my_motion_group",), "5"),
            ("equal", ("20 - foo",), "20"),
            ("equal", ("20 - <Hades>    n21x21",), "20"),
            ("is", ("five",), None),
            ("is", ("A - my_motion_group",), None),
            ("is", ("5 ~ my_motion_group",), None),
        ]
        for assert_type, args, expected in _conditions:
            with self.subTest(assert_type=assert_type, args=args, expected=expected):
                if assert_type == "equal":
                    self.assertEqual(_map.get_config_id(*args), expected)
                elif assert_type == "is":
                    self.assertIs(_map.get_config_id(*args), expected)
                else:
                    self.fail(f"Test assert_type '{assert_type}' is unknown.")

    def assert_runner(
        self,
        _assert: Union[str, Callable],
        attr: Callable,
        args: tuple,
        kwargs: dict,
        expected,
    ):
        with self.subTest(
            test_attr=attr,
            args=args,
            kwargs=kwargs,
            expected=expected,
        ):
            if isinstance(_assert, str) and hasattr(self, _assert):
                _assert = getattr(self, _assert)
            elif isinstance(_assert, str):
                self.fail(
                    f"The given assert name '{_assert}' does NOT match an "
                    f"assert method on self."
                )

            if _assert is self.assertRaises:
                with self.assertRaises(expected):
                    attr(*args, **kwargs)
            else:
                _assert(attr(*args, **kwargs), expected)
