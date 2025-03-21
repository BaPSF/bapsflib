import unittest as ut
from typing import Callable, Union

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
            self.assert_runner(
                _assert=self.assertEqual,
                attr=_map._generate_config_name,
                args=args,
                kwargs={},
                expected=expected,
            )

    def test_split_config_name(self):
        _map = self.MAP_CLASS
        _conditions = [
            # (_assert, args, expected)
            (self.assertEqual, ("5 - my_motion_group",), ("5", "my_motion_group")),
            (self.assertEqual, ("20 - foo",), ("20", "foo")),
            (self.assertEqual, ("20 - <Hades>    n21x21",), ("20", "<Hades>    n21x21")),
            (self.assertIs, ("five",), None),
            (self.assertIs, ("A - my_motion_group",), None),
            (self.assertIs, ("5 ~ my_motion_group",), None),
        ]
        for _assert, args, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map._split_config_name,
                args=args,
                kwargs={},
                expected=expected,
            )

    def test_get_dataset(self):
        _map = self.map
        _group = self.dgroup

        _conditions = [
            # (_assert, args, expected)
            (self.assertEqual, ("main",), _group["Run time list"]),
            (self.assertEqual, ("axis_names",), _group["bmotion_axis_names"]),
            (self.assertEqual, ("positions",), _group["bmotion_positions"]),
            (self.assertEqual, ("target_positions",), _group["bmotion_target_positions"]),
            (self.assertRaises, ("not_a_dataset",), ValueError),
        ]
        for _assert, args, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map._get_dataset,
                args=args,
                kwargs={},
                expected=expected,
            )

    def test_construct_dataset_name(self):
        _map = self.map
        _conditions = [
            # (_assert, args, expected)
            (self.assertEqual, ("main", ), "Run time list"),
            (self.assertEqual, ("axis_names",), "bmotion_axis_names"),
            (self.assertEqual, ("positions",), "bmotion_positions"),
            (self.assertEqual, ("target_positions",), "bmotion_target_positions"),
            (self.assertRaises, ("not_a_dataset",), ValueError),
        ]
        for _assert, args, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map.construct_dataset_name,
                args=args,
                kwargs={},
                expected=expected,
            )

    def test_get_config_id(self):
        _map = self.map
        _conditions = [
            # (_assert, args, expected)
            (self.assertEqual, ("5 - my_motion_group",), "5"),
            (self.assertEqual, ("20 - foo",), "20"),
            (self.assertEqual, ("20 - <Hades>    n21x21",), "20"),
            (self.assertIs, ("five",), None),
            (self.assertIs, ("A - my_motion_group",), None),
            (self.assertIs, ("5 ~ my_motion_group",), None),
        ]
        for assert_type, args, expected in _conditions:
            with self.subTest(assert_type=assert_type, args=args, expected=expected):
                if assert_type == "equal":
                    self.assertEqual(_map.get_config_id(*args), expected)
                elif assert_type == "is":
                    self.assertIs(_map.get_config_id(*args), expected)
                else:
                    self.fail(f"Test assert_type '{assert_type}' is unknown.")
        for _assert, args, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map.get_config_id,
                args=args,
                kwargs={},
                expected=expected,
            )

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

            if _assert == self.assertRaises:
                with self.assertRaises(expected):
                    attr(*args, **kwargs)
            else:
                _assert(attr(*args, **kwargs), expected)
