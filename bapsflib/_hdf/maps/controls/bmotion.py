"""
Module for the "bmotion" motion control mapper
`~bapsflib._hdf.maps.controls.bmotion.HDFMapControlBMotion`.
"""

__all__ = ["HDFMapControlBMotion"]

import copy
import numpy as np
import re
import warnings

from bapsf_motion.utils import toml
from h5py import Dataset, Group
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from bapsflib._hdf.maps.controls.templates import HDFMapControlTemplate
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib.utils import _bytes_to_str
from bapsflib.utils.exceptions import HDFMappingError
from bapsflib.utils.warnings import HDFMappingWarning


class HDFMapControlBMotion(HDFMapControlTemplate):
    """
    Mapping module for the control device 'bmotion'.

    Simple group structure looks like:

    .. code-block:: none

        +-- bmotion
        |   +-- <configuration name>        [Group]
        |   +-- Run time list               [Dataset]
        |   +-- bmotion_axis_names          [Dataset]
        |   +-- bmotion_positions           [Dataset]
        |   +-- bmotion_target_positions    [Dataset]

    """

    _contype = ConType.MOTION
    _required_dataset_names = {
        "main": "Run time list",
        "axis_names": "bmotion_axis_names",
        "positions": "bmotion_positions",
        "target_positions": "bmotion_target_positions",
    }

    def _init_before_build_configs(self):
        self._config_groups = []  # type: List[Group]
        # self._run_configs = None

    def _build_configs(self):
        # Build the attribute self.configs dictionary
        #
        self._verify_datasets()  # datasets must be verified before groups
        self._verify_groups()

        for group in self._config_groups:
            self._process_run_config_group(group)

        self._verify_multiple_run_config()

        # TODO: add HDFMappingError if self.configs is null

        # grab first n_mg_config rows of each dataset
        dset_axis_names = self.group[self.construct_dataset_name(which="axis_names")][
            :n_mg_configs
        ]

        # Build out each config
        for cname, _config in self.configs.items():  # type: str, dict
            mg_name = _config["MG_CONFIG"]["name"]

            # add 'dset paths' key
            _config["dset paths"] = tuple(
                self.group[dset_name].name
                for dset_name in self._required_dataset_names.values()
            )

            # add 'shotnum' key
            _config["shotnum"] = {
                "dset paths": None,
                "dset field": ("Shot number",),
                "shape": (),
                "dtype": np.int32,
            }

            # get axis names
            indices = np.where(
                dset_axis_names["motion_group_name"] == bytes(mg_name, encoding="utf-8")
            )
            if len(indices[0]) == 0:
                warnings.warn(
                    f"Unable to locate the '{mg_name}' configuration in the "
                    f"'bmotion_axis_names' dataset.",
                    HDFMappingWarning,
                )
                continue
            index = indices[0][0]
            ax_name_mapping = []
            for col_name in {"a0", "a1", "a2", "a3", "a4", "a5"}:

                ax_name = dset_axis_names[col_name][index]
                if ax_name == b"":
                    # this axis was not used
                    continue

                ax_name_mapping.append((col_name, _bytes_to_str(ax_name)))
            if len(ax_name_mapping) == 0:
                warnings.warn(
                    f"Unable to identify any used axes for the {mg_name}"
                    f" motion group configuration.",
                    HDFMappingWarning,
                )
                continue

            # add state values
            _config["state values"] = dict()
            for col_name, ax_name in ax_name_mapping:

                # add "position" 'state values'
                dset = self.group[self.construct_dataset_name(which="positions")]
                _key, _entry = self._generate_state_entry(
                    col_name=col_name,
                    ax_name=ax_name,
                    dset=dset,
                    state_dict=_config["state values"],
                )
                _config["state values"][_key] = _entry

                # add "target_position" ' state values
                dset = self.group[self.construct_dataset_name(which="target_positions")]
                _key, _entry = self._generate_state_entry(
                    col_name=col_name,
                    ax_name=ax_name,
                    dset=dset,
                    state_dict=_config["state values"],
                    ax_rename=lambda x: f"{x}_target",
                )
                _config["state values"][_key] = _entry

            # update config
            self.configs[cname] = _config

        # check all configs define a 'state values' entry
        for cname in list(self.configs.keys()):
            if "state values" not in self.configs[cname]:
                del self.configs[cname]
        if len(self.configs) == 0:
            raise HDFMappingError(
                device_name="bmotion",
                why="Unable to fully build any of the motion group configurations.",
            )

    def _verify_datasets(self):
        # bmotion group contains 4 datasets
        # - "Run time list" <dataset> --> top level data, mg names and motion list index
        # - "bmotion_axis_names" <dataset> --> LaPD axis associations
        # - "bmotion_positions" <dataset> --> motion group position data
        # - "bmotion_target_positions <dataset> --> motion group target position data
        #
        # verify datasets existence
        dataset_names = set(self.dataset_names)
        required_datasets = set(self._required_dataset_names.values())
        _remainder_dsets = required_datasets - dataset_names
        if len(_remainder_dsets) != 0:
            raise HDFMappingError(
                device_name="bmotion",
                why=f"Missing datasets {_remainder_dsets}.",
            )
        if len(dataset_names) != 4:
            raise HDFMappingError(
                device_name="bmotion",
                why=f"Expected 4 datasets, found {len(dataset_names)} datasets.",
            )

        # verify dataset structure
        for dset_name in self._required_dataset_names.values():
            dset = self.group[dset_name]
            if dset.dtype.fields is None:
                raise HDFMappingError(
                    device_name="bmotion",
                    why=f"Dataset {dset.name} does not have named columns.",
                )

            if dset_name == "Run time list":
                column_names = {"Shot number", "Configuration name"}
            else:
                column_names = {
                    "Shot number",
                    "motion_group_id",
                    "motion_group_name",
                    "motionlist_index",
                    "a0",
                    "a1",
                    "a2",
                    "a3",
                    "a4",
                    "a5",
                }

            if len(column_names - set(dset.dtype.fields)) != 0:
                raise HDFMappingError(
                    device_name="bmotion",
                    why=(
                        f"Dataset {dset.name} does not have all required columns,"
                        f" {column_names}."
                    ),
                )

    def _verify_groups(self):
        # bmotion group contains 1 group
        # - <group> --> contains the run configuration
        #
        group_names = self.subgroup_names
        if len(group_names) < 1:
            raise HDFMappingError(
                device_name="bmotion",
                why=f"Expected at least 1 sub-group, found {len(group_names)} groups.",
            )

        for ii, name in enumerate(group_names):
            group = self.group[name]
            if "RUN_CONFIG" not in group.attrs:
                continue

            self._config_groups.append(group)

        dset_runtime_list = self._get_dataset(which="main")  # Run-time list
        used_config_names = np.unique(dset_runtime_list["Configuration name"])
        for ii in range(len(self._config_groups)):
            config_name = Path(self._config_groups[ii].name).stem
            if config_name not in used_config_names:
                self._config_groups.pop(ii)

        if len(self._config_groups) == 0:
            raise HDFMappingError(
                device_name="bmotion",
                why="There are no valid configurations in the bmotion group.",
            )

    def _process_run_config_group(self, group: Group):
        # retrieve meta-info from config group
        _info = dict(group.attrs)  # type: Dict[str, Any]
        for key in _info.keys():
            _info[key] = _bytes_to_str(_info[key])
        _info["RUN_CONFIG"] = toml.loads(_info["RUN_CONFIG"])
        _run_config = _info.pop("RUN_CONFIG")  # type: Dict[str, Any]

        # initialize motion group configs
        mg_configs = _run_config["run"]["motion_group"]
        n_mg_configs = len(mg_configs)
        if n_mg_configs == 0:
            # no configs to add
            return

        for key, mg_config in mg_configs.items():
            name = self._generate_config_name(key, mg_config["name"])

            entry = {
                **_info,
                "mg_id": key,
                "MG_CONFIG": copy.deepcopy(mg_config),
                "RUN_CONFIG_NAME": Path(group.name).stem,
            },
            if name in self.configs:
                self.configs[name]["meta"] += (entry,)
            else:
                self.configs[name] = {}
                self.configs[name]["meta"] = (entry,)

    def _verify_multiple_run_config(self):
        if len(self._config_groups) == 1:
            return
        elif len(self._config_groups) == 0:
            raise HDFMappingError(
                device_name="bmotion",
                why="There are no valid configurations in the bmotion group.",
            )

        # If a motion group name is used in multiple run configurations,
        # then it must the same bmotion_axis_names entries.  Otherwise,
        # these were two different probe drives with different run-time
        # states, which can NOT be handled by bapsflib at the moment.
        for config_name in list(self.configs.keys()):
            config_dict = self.configs[config_name]
            if len(config_dict["meta"]) == 0:
                self.configs.pop(config_name)
                continue
            elif len(config_dict["meta"]) == 1:
                continue

            # multiple run configurations were used for this motion group
            # must check that they have the same bmotion_axis_names entry

            self._verify_consistent_motion_group_run_time_state(config_name)

    def _verify_consistent_motion_group_run_time_state(self, config_name):
        # config_name is a configuration name in self.configs
        config_dict = self.configs[config_name]

        rtl_dset = self.group[self.construct_dataset_name(which="main")]
        axn_dset = self.group[self.construct_dataset_name(which="axis_names")]

        axis_names = {
            "a0": None, "a1": None, "a2": None, "a3": None, "a4": None, "a5": None
        }  # type: Dict[str, Union[str, None]]
        remove_config = False
        for ii, entry in enumerate(list(config_dict["meta"])):
            run_config_name = entry["RUN_CONFIG_NAME"]

            indices = np.where(
                rtl_dset["Configuration name"] == run_config_name.encode("utf-8")
            )[0]
            if indices.size == 0:
                warnings.warn(
                    f"bmotion run configuration '{run_config_name}' was not "
                    f"found in the 'Run time list' dataset.  Removing "
                    f"configuration from association with motion group "
                    f"'{config_name}'.",
                    HDFMappingWarning,
                )
                meta_list = list(config_dict["meta"])
                meta_list.pop(ii)
                config_dict["meta"] = meta_list
                continue

            data_row = axn_dset[indices[0]]
            for col_name in axis_names.keys():
                ax_name = _bytes_to_str(data_row[col_name])
                if axis_names[col_name] is None:
                    axis_names[col_name] = ax_name
                elif axis_names[col_name] != ax_name:
                    warnings.warn(
                        f"bmotion: the motion group '{config_name}' has differing "
                        f"axis names for the specified run configurations.  Removing "
                        f"'{config_name}' from mapping.",
                        HDFMappingWarning,
                    )
                    remove_config = True
                    break

            if remove_config:
                break

        if len(config_dict["meta"]) == 0:
            warnings.warn(
                f"bmotion: unable to fully map the motion group '{config_name}'.  "
                f"Removing from mapping.",
                HDFMappingWarning,
            )
            self.configs.pop(config_name)
        elif remove_config:
            self.configs.pop(config_name)
        else:
            self.configs[config_name] = config_dict

    @staticmethod
    def _generate_state_entry(
        col_name: str,
        ax_name: str,
        dset: Dataset,
        state_dict: dict,
        ax_rename: Optional[Callable] = None,
    ):
        """
        Generate a dictionary configuration for the `'state values'`
        of the :attr:`configs` dictionary.

        Parameters
        ----------
        col_name : `str`
            Name of the column in ``dset`` to generate the entry for.

        ax_name : `str`
            The `'state values'` key the generated entry will map to.
            If given `'x'`, `'y'`, or `'z'`, then they will
            automatically map to the `'xyz'` states value key.

        dset : `Dataset`
            `h5py.Dataset` to be examined to generate the state values
            entry.

        state_dict : `dict`
            A starting dictionary for the state values entry.

        ax_rename : Optional[Callable]
            A callable that will rename ``ax_name`` to define the
            state values key. For example, ``lambda x: f'target_{x}'``
            would generate a ``'target_xyz'`` key if ``ax_name='x'``
            or ``'target_rotation'`` key if ``'ax_name='rotation'``.
            (DEFAULT `None`)
        """
        if ax_rename is None:

            def ax_rename(x):
                return x

        if ax_name.casefold() in ("x", "y", "z"):
            ax_name = ax_name.casefold()
            state_key = ax_rename("xyz")
            state_entry = state_dict.get(state_key, None)

            if state_entry is None:
                state_entry = {
                    "dset paths": (dset.name,),
                    "dset field": ("", "", ""),
                    "shape": (3,),
                    "dtype": np.float64,
                    "config column": "motion_group_name",
                }

            dset_field = list(state_entry["dset field"])
            if ax_name == "x":
                dset_field[0] = col_name
            elif ax_name == "y":
                dset_field[1] = col_name
            else:
                dset_field[2] = col_name
            state_entry["dset field"] = tuple(dset_field)

        else:
            state_key = ax_rename(ax_name)
            state_entry = {
                "dset paths": (dset.name,),
                "dset field": (col_name,),
                "shape": (),
                "dtype": dset.dtype[col_name],
                "config column": "motion_group_name",
            }

        return state_key, state_entry

    @staticmethod
    def _generate_config_name(key, mg_name):
        """
        Generate the configuration name, which is a mash-up of the
        motion group key and name in the `bapsf_motion` run manager
        configuration.
        """
        # return f"{key} - {mg_name}"
        return f"{mg_name}"

    @staticmethod
    def _split_config_name(config_name):
        """
        Splits a configuration name into its motion group key and name.
        """
        # match = re.compile(r"\s*(?P<_id>[0-9]+)\s+(-)\s+(?P<mg_name>.+)").fullmatch(
        #     config_name
        # )
        # return (
        #     None
        #     if match is None
        #     else (match.group("_id").strip(), match.group("mg_name").strip())
        # )
        return None, config_name

    def _get_dataset(self, which: str) -> Dataset:
        """
        Retrieves the ``bmotion`` group dataset based on the ``which``
        argument.  The ``which`` argument should map directly to the
        keys of :attr:`_required_dataset_names`.
        """
        name = self.construct_dataset_name(which=which)
        return self.group[name]

    def construct_dataset_name(self, which: str, *args) -> str:
        """
        Return the data set name for the specified ``which`` argument.
        The ``which`` argument should map directly to the
        keys of :attr:`_required_dataset_names`.
        """
        try:
            name = self._required_dataset_names[which]
        except KeyError:
            raise ValueError(
                f"The requested dataset is invalid, got request '{which}'"
                f" and valid requests are {self._required_dataset_names.keys()}."
            )
        return name

    def get_config_id(self, config_name: str) -> str:
        """
        Get the configuration "motion group" id for the specified
        ``config_name``.
        """
        id_and_mg_name = self._split_config_name(config_name)
        return None if id_and_mg_name is None else id_and_mg_name[0]

    def get_config_name_by_drive_name(self, name: str) -> Union[str, None]:
        """
        Get the configuration name for the specified drive ``name``.
        """
        if not isinstance(name, str):
            return None

        _mg_configs = self._run_config["run"]["motion_group"]
        for key, _config in _mg_configs.items():
            if _config["drive"]["name"] == name:
                config_name = self._generate_config_name(key, _config["name"])
                return config_name

        return None

    def get_config_name_by_motion_group_id(
        self, _id: Union[int, str]
    ) -> Union[str, None]:
        """
        Get the configuration name for the given motion group id.
        """
        if not isinstance(_id, (int, str)):
            return None
        elif isinstance(_id, int):
            _id = f"{_id}"

        _mg_configs = self._run_config["run"]["motion_group"]
        try:
            mg_name = _mg_configs[_id]["name"]
            config_name = self._generate_config_name(_id, mg_name)
            return config_name
        except KeyError:
            pass

    def get_config_name_by_motion_group_name(self, name: str) -> Union[str, None]:
        """
        Get the configuration name for the given motion group name.
        """
        if not isinstance(name, str):
            return None

        _mg_configs = self._run_config["run"]["motion_group"]
        for key, _config in _mg_configs.items():
            if _config["name"] == name:
                config_name = self._generate_config_name(key, _config["name"])
                return config_name

        return None
