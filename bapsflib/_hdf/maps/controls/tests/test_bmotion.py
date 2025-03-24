import h5py
import numpy as np
import unittest as ut

from bapsf_motion.utils import toml
from typing import Callable, Union

from bapsflib._hdf.maps.controls.bmotion import HDFMapControlBMotion
from bapsflib._hdf.maps.controls.tests.common import ControlTestCase
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib.utils.exceptions import HDFMappingError


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

    def test_raises_too_many_subgroups(self):
        _group = self.dgroup  # type: h5py.Group
        _group.create_group("extra_group")
        with self.assertRaises(HDFMappingError):
            _map = self.map

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

    def test_raises_required_datasets_have_no_fields(self):
        for dset_name in self.MAP_CLASS._required_dataset_names.values():
            self.f.remove_all_modules()
            self.f.add_module(self.DEVICE_NAME)

            _group = self.dgroup  # type: h5py.Group
            del _group[dset_name]

            _group.create_dataset(dset_name, data=np.linspace(0, 10, 1))

            with self.subTest(name=dset_name), self.assertRaises(HDFMappingError):
                _map = self.map

    def test_raises_datasets_missing_fields(self):
        for dset_name in self.MAP_CLASS._required_dataset_names.values():
            self.f.remove_all_modules()
            self.f.add_module(self.DEVICE_NAME)

            _group = self.dgroup
            dset = _group[dset_name]
            data = dset[...]  # type: np.ndarray
            del _group[dset_name]
            field_names = list(data.dtype.names)
            _group.create_dataset(dset_name, data=data[field_names[1:]])

            with self.subTest(name=dset_name), self.assertRaises(HDFMappingError):
                _map = self.map

    def test_raises_missing_run_config(self):
        _group = self.dgroup  # type: h5py.Group
        for child in _group.values():
            if isinstance(child, h5py.Group) and "RUN_CONFIG" in child.attrs:
                del child.attrs["RUN_CONFIG"]
                break

        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_raises_run_config_has_no_motion_groups(self):
        _group = self.dgroup
        _run_config_str = None
        child = None
        for child in _group.values():
            if isinstance(child, h5py.Group) and "RUN_CONFIG" in child.attrs:
                _run_config_str = child.attrs["RUN_CONFIG"]
                break

        if _run_config_str is None:
            self.fail("Unable to find RUN_CONFIG in configuration subgroup.")

        _run_config = toml.loads(_run_config_str)
        _run_config["run"]["motion_group"] = {}
        child.attrs["RUN_CONFIG"] = toml.as_toml_string(_run_config)

        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_raise_build_config_ends_with_no_configs(self):
        # at the end of _build_configs self.configs is still empty
        self.fail("write test")

    def test_warns_config_not_in_datasets(self):
        # config defined in "RUN_CONFIG" is missing from datasets
        self.fail("write test")

    def test_warns_axis_names_not_defined(self):
        # axis names are not populated in bmotion_axis_names
        self.fail("write test")

    def test_generate_state_entry(self):
        _map = self.map  # type: HDFMapControlBMotion
        _dset = self.dgroup["bmotion_positions"]  # type: h5py.Dataset
        _conditions = [
            # (_assert, kwargs, expected)
            (
                self.assertEqual,
                {
                    "col_name": "a0",
                    "ax_name": "x",
                    "dset": _dset,
                    "state_dict": {},
                },
                (
                    "xyz",
                    {
                        "dset paths": (_dset.name,),
                        "dset field": ("a0", "", ""),
                        "shape": (3,),
                        "dtype": np.float64,
                        "config column": "motion_group_id",
                    },
                ),
            ),
            (
                self.assertEqual,
                {
                    "col_name": "a1",
                    "ax_name": "y",
                    "dset": _dset,
                    "state_dict": {"target_xyz": {}},
                },
                (
                    "xyz",
                    {
                        "dset paths": (_dset.name,),
                        "dset field": ("", "a1", ""),
                        "shape": (3,),
                        "dtype": np.float64,
                        "config column": "motion_group_id",
                    },
                ),
            ),
            (
                self.assertEqual,
                {
                    "col_name": "a2",
                    "ax_name": "z",
                    "dset": _dset,
                    "state_dict": {
                        "xyz": {
                            "dset paths": (_dset.name,),
                            "dset field": ("a0", "", ""),
                            "shape": (3,),
                            "dtype": np.float64,
                            "config column": "motion_group_id",
                        },
                    },
                },
                (
                    "xyz",
                    {
                        "dset paths": (_dset.name,),
                        "dset field": ("a0", "", "a2"),
                        "shape": (3,),
                        "dtype": np.float64,
                        "config column": "motion_group_id",
                    },
                ),
            ),
            (
                self.assertEqual,
                {
                    "col_name": "a4",
                    "ax_name": "rotation",
                    "dset": _dset,
                    "state_dict": {},
                },
                (
                    "rotation",
                    {
                        "dset paths": (_dset.name,),
                        "dset field": ("a4",),
                        "shape": (),
                        "dtype": _dset.dtype["a4"],
                        "config column": "motion_group_id",
                    },
                ),
            ),
        ]
        for _assert, kwargs, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map._generate_state_entry,
                args=(),
                kwargs=kwargs,
                expected=expected,
            )

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
            (self.assertEqual, ("main",), "Run time list"),
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
        for _assert, args, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map.get_config_id,
                args=args,
                kwargs={},
                expected=expected,
            )

    def test_get_config_name_by_drive_name(self):
        _map = self.map  # type: HDFMapControlBMotion
        _conditions = [
            (self.assertIs, (5,), None),
            (self.assertIs, ("not_correct_drive_name",), None),
            (self.assertEqual, ("drive0",), _map._generate_config_name(0, "mg0")),
        ]
        for _assert, args, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map.get_config_name_by_drive_name,
                args=args,
                kwargs={},
                expected=expected,
            )

    def test_get_config_name_by_motion_group_id(self):
        _map = self.map  # type: HDFMapControlBMotion
        _conditions = [
            # (_assert, args, expected)
            (self.assertIs, (5.5,), None),
            (self.assertIs, ({"not_an_id": 5},), None),
            (self.assertIs, ("not_correct_motion_group_id",), None),
            (self.assertEqual, (0,), _map._generate_config_name(0, "mg0")),
            (self.assertEqual, ("0",), _map._generate_config_name(0, "mg0")),
        ]
        for _assert, args, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map.get_config_name_by_motion_group_id,
                args=args,
                kwargs={},
                expected=expected,
            )

    def test_get_config_name_by_motion_group_name(self):
        _map = self.map  # type: HDFMapControlBMotion
        _conditions = [
            # (_assert, args, expected)
            (self.assertIs, (5.5,), None),
            (self.assertIs, ({"not_a_name": 5},), None),
            (self.assertIs, ("wrong_name",), None),
            (self.assertEqual, ("mg0",), _map._generate_config_name(0, "mg0")),
        ]
        for _assert, args, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map.get_config_name_by_motion_group_name,
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
