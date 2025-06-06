import h5py
import numpy as np
import unittest as ut
import unittest.mock
import warnings

from bapsf_motion.utils import toml

from bapsflib._hdf.maps.controls.bmotion import HDFMapControlBMotion
from bapsflib._hdf.maps.controls.tests.common import ControlTestCase
from bapsflib._hdf.maps.controls.tests.fauxbmotion import FauxBMotion
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib.utils import _bytes_to_str
from bapsflib.utils.exceptions import HDFMappingError
from bapsflib.utils.warnings import HDFMappingWarning


class TestBMotion(ControlTestCase):
    """Test class for HDFMapControlBMControl"""

    # define setup variables
    DEVICE_NAME = "bmotion"
    DEVICE_PATH = "Raw data + config/bmotion"
    MAP_CLASS = HDFMapControlBMotion
    CONTYPE = ConType.MOTION

    @property
    def map(self) -> HDFMapControlBMotion:
        return super().map

    @property
    def mod(self) -> FauxBMotion:
        return super().mod

    def test_attribute_existence(self):
        _map = self.map
        _attributes_names = [
            "run_config_names",
            "get_config_name_by_drive_name",
            "get_config_name_by_motion_group_id",
            "get_config_name_by_motion_group_name",
            "get_run_configuration",
        ]
        for name in _attributes_names:
            with self.subTest(attr_name=name):
                self.assertTrue(hasattr(_map, name))

    def test_property_existence(self):
        _map = self.map
        _property_names = ["run_config_names"]
        for name in _property_names:
            with self.subTest(property_name=name):
                self.assertIsInstance(getattr(type(_map), name), property)

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

    def test_raises_no_subgroups(self):
        _group = self.dgroup  # type: h5py.Group
        for key, element in _group.items():
            if isinstance(element, h5py.Group):
                del _group[key]

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
            _group = self.dgroup
            dset = _group[dset_name]
            data = dset[...]  # type: np.ndarray
            del _group[dset_name]
            field_names = list(data.dtype.names)
            _group.create_dataset(dset_name, data=data[field_names[1:]])

            with self.subTest(name=dset_name), self.assertRaises(HDFMappingError):
                _map = self.map

            self.mod.knobs.reset()

    def test_raises_missing_run_config(self):
        # for some unknown reason, coverage results are not being produced
        # for this test when executed during the whole class execution,
        # unless we manually tear down and set up
        self.tearDown()
        self.setUp()

        _group = self.dgroup  # type: h5py.Group
        for child in _group.values():
            if isinstance(child, h5py.Group) and "RUN_CONFIG" in child.attrs:
                del child.attrs["RUN_CONFIG"]
                break

        with self.assertRaises(HDFMappingError):
            _map = self.map

    def test_raises_run_config_has_no_motion_groups(self):
        # for some unknown reason, coverage results are not being produced
        # for this test when executed during the whole class execution,
        # unless we manually tear down and set up
        self.tearDown()
        self.setUp()

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
        with ut.mock.patch.object(HDFMapControlBMotion, "configs") as mock_configs:
            mock_configs.return_value = {}
            with self.assertRaises(HDFMappingError):
                _map = self.map

    def test_warns_config_not_in_datasets(self):
        # config defined in "RUN_CONFIG" is missing from datasets
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
        n_motion_groups = len(_run_config["run"]["motion_group"])
        _run_config["run"]["motion_group"][f"{n_motion_groups}"] = {
            "name": "unused motion group",
            "drive": {"name": "unused drive"},
        }
        child.attrs["RUN_CONFIG"] = toml.as_toml_string(_run_config)

        # test
        with self.assertWarns(HDFMappingWarning):
            _map = self.map  # type: HDFMapControlBMotion
            self.assertTrue(
                _map._generate_config_name(n_motion_groups, "unused motion group")
                not in _map.configs
            )

    def test_warns_axis_names_not_defined(self):
        # axis names are not populated in bmotion_axis_names
        _group = self.dgroup
        dset_axis_names = _group["bmotion_axis_names"]
        data = dset_axis_names[...]
        data[["a0", "a1", "a2", "a3", "a4", "a5"]][:] = b""
        dset_axis_names[...] = data[...]

        # test
        with self.assertRaises(HDFMappingError):
            with self.assertWarns(HDFMappingWarning):
                _map = self.map  # type: HDFMapControlBMotion

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
                        "config column": "motion_group_name",
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
                        "config column": "motion_group_name",
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
                            "config column": "motion_group_name",
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
                        "config column": "motion_group_name",
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
                        "config column": "motion_group_name",
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
            (self.assertEqual, ("five",), (None, "five")),
            (self.assertEqual, ("A - my_motion_group",), (None, "A - my_motion_group")),
            (self.assertEqual, ("5 ~ my_motion_group",), (None, "5 ~ my_motion_group")),
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

    def test_get_config_column_value(self):
        _map = self.map
        with ut.mock.patch.object(
            self.MAP_CLASS, "process_config_name", side_effect=_map.process_config_name
        ) as mock_attr:
            self.assertEqual(_map.get_config_column_value("0 - mg0"), "mg0")
            self.assertTrue(mock_attr.called)

    def test_get_config_name_by_drive_name(self):
        _map = self.map  # type: HDFMapControlBMotion
        _conditions = [
            # (assert, args, expected)
            (self.assertRaises, (5,), TypeError),
            (self.assertRaises, ("not_correct_drive_name",), ValueError),
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
        _map = self.map
        _conditions = [
            # (_assert, args, expected)
            (self.assertRaises, (5.5,), TypeError),
            (self.assertRaises, ({"not_an_id": 5},), TypeError),
            (self.assertRaises, ("not_correct_motion_group_id",), HDFMappingError),
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

    def test_get_config_name_by_motion_group_id_w_multiple_run_configs(self):
        self.mod.knobs.n_run_configs = 3
        self.mod.knobs.n_motion_groups = 1
        run_config_names = self.mod.run_configuration_names

        mock_configs_dict = {
            "0 - mg0": {
                "meta": ({"MG_ID": "0", "RUN_CONFIG_NAME": run_config_names[0]},)
            },
            "mg1": {"meta": ({"MG_ID": "1", "RUN_CONFIG_NAME": run_config_names[0]},)},
            "0 - <Hades> xline": {
                "meta": ({"MG_ID": "0", "RUN_CONFIG_NAME": run_config_names[1]},)
            },
            "0 - <Hera> yline": {
                "meta": ({"MG_ID": "0", "RUN_CONFIG_NAME": run_config_names[2]},)
            },
        }
        _map = self.map
        _conditions = [
            # (_assert, args, expected)
            (self.assertRaises, (0,), HDFMappingError),
        ]
        with (
            ut.mock.patch.dict(_map.configs, mock_configs_dict),
            self.assertRaises(HDFMappingError),
        ):
            _map.get_config_name_by_motion_group_id(0)

    def test_get_config_name_by_motion_group_name(self):
        _map = self.map  # type: HDFMapControlBMotion
        _conditions = [
            # (_assert, args, expected)
            (self.assertRaises, (5.5,), TypeError),
            (self.assertRaises, ({"not_a_name": 5},), TypeError),
            (self.assertRaises, ("wrong_name",), ValueError),
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

    def test_get_config_name_by_motion_group_name_w_multiple_run_configs(self):
        self.mod.knobs.n_run_configs = 2
        self.mod.knobs.n_motion_groups = 2

        _map = self.map
        self.assertEqual(_map.get_config_name_by_motion_group_name("mg0"), "mg0")

    def test_configs_one_motion_group(self):
        _group = self.dgroup
        _faux_mod = self.mod  # type: FauxBMotion

        _map = self.map
        configs = _map.configs

        _run_config_str = _group[_faux_mod.run_configuration_names[0]].attrs["RUN_CONFIG"]
        _run_config = toml.loads(_run_config_str)
        _mg_config = _run_config["run"]["motion_group"]["0"]

        _conditions = [
            # (_assert, value, expected)
            (self.assertEqual, 1, len(configs)),
            (self.assertIn, "0 - mg0", configs),
            (self.assertIn, "BAPSFDAQ_MOTION_LV_VERSION", configs["0 - mg0"]),
            (self.assertIn, "BAPSF_MOTION_VERSION", configs["0 - mg0"]),
            (self.assertIn, "EXPANSION_ATTR", configs["0 - mg0"]),
            (self.assertIn, "MG_CONFIG", configs["0 - mg0"]),
            (self.assertIn, "dset paths", configs["0 - mg0"]),
            (self.assertIn, "shotnum", configs["0 - mg0"]),
            (self.assertIn, "state values", configs["0 - mg0"]),
            (
                self.assertIsInstance,
                configs["0 - mg0"]["BAPSFDAQ_MOTION_LV_VERSION"],
                str,
            ),
            (self.assertIsInstance, configs["0 - mg0"]["BAPSF_MOTION_VERSION"], str),
            (self.assertIsInstance, configs["0 - mg0"]["EXPANSION_ATTR"], str),
            (self.assertIsInstance, configs["0 - mg0"]["MG_CONFIG"], dict),
            (self.assertIsInstance, configs["0 - mg0"]["dset paths"], tuple),
            (self.assertIsInstance, configs["0 - mg0"]["shotnum"], dict),
            (self.assertIsInstance, configs["0 - mg0"]["state values"], dict),
            (self.assertDictEqual, configs["0 - mg0"]["MG_CONFIG"], _mg_config),
            (
                self.assertEqual,
                configs["0 - mg0"]["dset paths"],
                (
                    f"/Raw data + config/bmotion/Run time list",
                    f"/Raw data + config/bmotion/bmotion_axis_names",
                    f"/Raw data + config/bmotion/bmotion_positions",
                    f"/Raw data + config/bmotion/bmotion_target_positions",
                ),
            ),
            (
                self.assertDictEqual,
                configs["0 - mg0"]["shotnum"],
                {
                    "dset paths": None,
                    "dset field": ("Shot number",),
                    "shape": (),
                    "dtype": np.int32,
                },
            ),
            (self.assertIn, "xyz", configs["0 - mg0"]["state values"]),
            (self.assertIn, "xyz_target", configs["0 - mg0"]["state values"]),
            (
                self.assertDictEqual,
                configs["0 - mg0"]["state values"]["xyz"],
                {
                    "dset paths": ("/Raw data + config/bmotion/bmotion_positions",),
                    "dset field": ("a0", "a1", ""),
                    "shape": (3,),
                    "dtype": np.float64,
                    "config column": "motion_group_name",
                },
            ),
            (
                self.assertDictEqual,
                configs["0 - mg0"]["state values"]["xyz_target"],
                {
                    "dset paths": (
                        "/Raw data + config/bmotion/bmotion_target_positions",
                    ),
                    "dset field": ("a0", "a1", ""),
                    "shape": (3,),
                    "dtype": np.float64,
                    "config column": "motion_group_name",
                },
            ),
        ]
        for (
            _assert,
            value,
            expected,
        ) in _conditions:
            with self.subTest(_assert=_assert.__name__, value=value, expected=expected):
                _assert(value, expected)

    def test_configs_two_motion_groups(self):
        _group = self.dgroup
        _faux_mod = self.mod  # type: FauxBMotion
        _faux_mod.knobs.n_motion_groups = 2

        _map = self.map
        configs = _map.configs

        _run_config_str = _group[_faux_mod.run_configuration_names[0]].attrs["RUN_CONFIG"]
        _run_config = toml.loads(_run_config_str)

        _conditions = [
            # (_assert, value, expected)
            (self.assertEqual, 2, len(configs)),
            (self.assertIn, "0 - mg0", configs),
            (self.assertIn, "1 - mg1", configs),
        ]
        for ii, mg_name in enumerate(("0 - mg0", "1 - mg1")):
            _conditions.extend(
                [
                    (self.assertIn, "BAPSFDAQ_MOTION_LV_VERSION", configs[mg_name]),
                    (self.assertIn, "BAPSF_MOTION_VERSION", configs[mg_name]),
                    (self.assertIn, "EXPANSION_ATTR", configs[mg_name]),
                    (self.assertIn, "MG_CONFIG", configs[mg_name]),
                    (self.assertIn, "dset paths", configs[mg_name]),
                    (self.assertIn, "shotnum", configs[mg_name]),
                    (self.assertIn, "state values", configs[mg_name]),
                    (
                        self.assertIsInstance,
                        configs[mg_name]["BAPSFDAQ_MOTION_LV_VERSION"],
                        str,
                    ),
                    (
                        self.assertIsInstance,
                        configs[mg_name]["BAPSF_MOTION_VERSION"],
                        str,
                    ),
                    (self.assertIsInstance, configs[mg_name]["EXPANSION_ATTR"], str),
                    (self.assertIsInstance, configs[mg_name]["MG_CONFIG"], dict),
                    (self.assertIsInstance, configs[mg_name]["dset paths"], tuple),
                    (self.assertIsInstance, configs[mg_name]["shotnum"], dict),
                    (self.assertIsInstance, configs[mg_name]["state values"], dict),
                    (
                        self.assertDictEqual,
                        configs[mg_name]["MG_CONFIG"],
                        _run_config["run"]["motion_group"][f"{ii}"],
                    ),
                    (
                        self.assertEqual,
                        configs[mg_name]["dset paths"],
                        (
                            f"/Raw data + config/bmotion/Run time list",
                            f"/Raw data + config/bmotion/bmotion_axis_names",
                            f"/Raw data + config/bmotion/bmotion_positions",
                            f"/Raw data + config/bmotion/bmotion_target_positions",
                        ),
                    ),
                    (
                        self.assertDictEqual,
                        configs[mg_name]["shotnum"],
                        {
                            "dset paths": None,
                            "dset field": ("Shot number",),
                            "shape": (),
                            "dtype": np.int32,
                        },
                    ),
                    (self.assertIn, "xyz", configs[mg_name]["state values"]),
                    (self.assertIn, "xyz_target", configs[mg_name]["state values"]),
                    (
                        self.assertDictEqual,
                        configs[mg_name]["state values"]["xyz"],
                        {
                            "dset paths": (
                                "/Raw data + config/bmotion/bmotion_positions",
                            ),
                            "dset field": ("a0", "a1", ""),
                            "shape": (3,),
                            "dtype": np.float64,
                            "config column": "motion_group_name",
                        },
                    ),
                    (
                        self.assertDictEqual,
                        configs[mg_name]["state values"]["xyz_target"],
                        {
                            "dset paths": (
                                "/Raw data + config/bmotion/bmotion_target_positions",
                            ),
                            "dset field": ("a0", "a1", ""),
                            "shape": (3,),
                            "dtype": np.float64,
                            "config column": "motion_group_name",
                        },
                    ),
                ],
            )
        for (
            _assert,
            value,
            expected,
        ) in _conditions:
            with self.subTest(_assert=_assert.__name__, value=value, expected=expected):
                _assert(value, expected)

    def test_configs_two_motion_groups_with_one_unused(self):
        # test a run configuration with two motion groups in RUN_CONFIGS
        # but with only one is saved to datasets
        _group = self.dgroup
        _faux_mod = self.mod  # type: FauxBMotion

        _run_config_str = _group[_faux_mod.run_configuration_names[0]].attrs["RUN_CONFIG"]
        _run_config = toml.loads(_run_config_str)
        _run_config["run"]["motion_group"]["1"] = {
            "name": "mg1",
            "drive": {"name": "drive1"},
        }
        _group[_faux_mod.run_configuration_names[0]].attrs["RUN_CONFIG"] = (
            toml.as_toml_string(_run_config)
        )

        with self.assertWarns(HDFMappingWarning):
            self.test_configs_one_motion_group()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=HDFMappingWarning)
            _map = self.map
            configs = _map.configs
        _conditions = [
            # (_assert, value, expected)
            (self.assertNotIn, "1 - mg1", configs),
        ]
        for _assert, value, expected in _conditions:
            with self.subTest(_assert=_assert.__name__, value=value, expected=expected):
                _assert(value, expected)

    def test_process_config_name(self):
        _map = self.map
        _config_name = list(_map.configs.keys())[0]
        _conditions = [
            # (assert, config_name, expected)
            (self.assertEqual, _config_name, _config_name),
            # probe drive names are nicknames (when uniquely used)
            (self.assertEqual, "drive0", _config_name),
        ]
        for _assert, config_name, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map.process_config_name,
                args=(config_name,),
                kwargs={},
                expected=expected,
            )

    def test_raises_process_config(self):
        _map = self.map

        # add a config that uses the same drive name
        _map.configs["<drive0> duplicate"] = {
            "meta": ({"DRIVE_NAME": "drive0"},),
        }
        _conditions = [
            # (assert, config_name, expecged)
            # bad nickname
            (self.assertRaises, "bad_nickname", ValueError),
            # drive not used uniquely
            (self.assertRaises, "drive0", ValueError),
        ]
        for _assert, config_name, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map.process_config_name,
                args=(config_name,),
                kwargs={},
                expected=expected,
            )

    def test_get_run_configuration(self):
        run_configuration_name = self.mod.run_configuration_names[0]
        run_config_group = self.dgroup[run_configuration_name]
        run_config_toml_string = _bytes_to_str(run_config_group.attrs["RUN_CONFIG"])
        run_config_toml_dict = toml.loads(run_config_toml_string)

        _map = self.map

        _conditions = [
            # (assert, kwargs, expected)
            (self.assertDictEqual, {}, run_config_toml_dict),
            (
                self.assertDictEqual,
                {"run_config_name": run_configuration_name},
                run_config_toml_dict,
            ),
            (
                self.assertEqual,
                {"as_toml_string": True},
                run_config_toml_string,
            ),
        ]
        for _assert, kwargs, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map.get_run_configuration,
                args=(),
                kwargs=kwargs,
                expected=expected,
            )

    def test_raises_get_run_configuration(self):
        run_configuration_name = self.mod.run_configuration_names[0]
        run_config_group = self.dgroup[run_configuration_name]
        self.dgroup.copy(run_config_group, self.dgroup, name="second_run_config")
        self.dgroup["Run time list"]["Configuration name", -1] = "second_run_config"

        _map = self.map

        _conditions = [
            # (assert, kwargs, expected)
            (self.assertRaises, {"as_toml_string": "not a bool"}, TypeError),
            (self.assertRaises, {"run_config_name": 5}, TypeError),
            # multiple run configs present, so need to specify
            (self.assertRaises, {"run_config_name": None}, ValueError),
            # bad run_config_name
            (self.assertRaises, {"run_config_name": "non-existent name"}, ValueError),
        ]
        for _assert, kwargs, expected in _conditions:
            self.assert_runner(
                _assert=_assert,
                attr=_map.get_run_configuration,
                args=(),
                kwargs=kwargs,
                expected=expected,
            )

    def test_run_config_names(self):
        _map = self.map
        run_config_name = self.mod.run_configuration_names[0]

        _conditions = [
            # (assert, expected)
            (self.assertIsInstance, tuple),
            (self.assertEqual, (run_config_name,)),
        ]
        for _assert, expected in _conditions:
            with self.subTest(_assert=_assert.__name__, expected=expected):
                _assert(_map.run_config_names, expected)

    def test_build_multiple_run_configs(self):
        self.mod.knobs.n_motion_groups = 3
        self.mod.knobs.n_run_configs = 2
        _map = self.map

        self.assertEqual(len(self.mod.motion_group_names), len(_map.configs.keys()))
        self.assertEqual(
            len(set(self.mod.motion_group_names) - set(_map.configs.keys())),
            0,
        )

    def test_run_config_missing_from_run_time_list(self):
        self.mod.knobs.n_motion_groups = 1
        self.mod.knobs.n_run_configs = 2
        self.mod.knobs.sn_size = 50

        # remove 2nd run config from "Run time list" dset
        data = self.dgroup["Run time list"][...]
        del self.dgroup["Run time list"]
        self.dgroup.create_dataset("Run time list", data=data[0:50])

        with self.assertWarns(HDFMappingWarning):
            _map = self.map
            self.assertTrue(
                all(len(config["meta"]) == 1 for config in _map.configs.values())
            )
            self.assertTrue(
                all(
                    config["meta"][0]["RUN_CONFIG_NAME"]
                    == self.mod.run_configuration_names[0]
                    for config in _map.configs.values()
                )
            )

    def test_multiple_run_w_inconsistent_axes(self):
        self.mod.knobs.n_motion_groups = 2
        self.mod.knobs.n_run_configs = 2
        self.mod.knobs.sn_size = 50

        second_run_name = self.mod.run_configuration_names[1]
        mg_name = "mg0"

        # make axes different for mg0 in 2nd run
        rtl_mask = np.repeat(
            self.dgroup["Run time list"]["Configuration name"]
            == second_run_name.encode(),
            2,
        )
        ban_mask = (
            self.dgroup["bmotion_axis_names"]["motion_group_name"] == mg_name.encode()
        )
        mask = np.logical_and(rtl_mask, ban_mask)
        self.dgroup["bmotion_axis_names"]["a1", mask] = b"Z"

        with self.assertWarns(HDFMappingWarning):
            _map = self.map
            self.assertNotIn(mg_name, _map.configs)
