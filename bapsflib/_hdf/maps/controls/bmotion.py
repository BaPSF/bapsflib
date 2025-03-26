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
from typing import Callable, Optional, Union

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
        self._run_config = None

    def _build_configs(self):
        # Build the attribute self.configs dictionary
        #
        # bmotion group contains 1 group and 4 datasets
        # - <group> --> contains the run configuration
        # - "Run time list" <dataset> --> top level data, mg names and motion list index
        # - "bmotion_axis_names" <dataset> --> LaPD axis associations
        # - "bmotion_positions" <dataset> --> motion group position data
        # - "bmotion_target_positions <dataset> --> motion group target position data
        #
        # examine groups
        group_names = self.subgroup_names
        if len(group_names) != 1:
            raise HDFMappingError(
                device_name="bmotion",
                why=f"Expected 1 sub-group, found {len(group_names)} groups.",
            )
        config_group = self.group[group_names[0]]  # type: Group

        # examine datasets
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

        # examine dataset structure
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

        # construct meta-info from config group
        _info = dict(config_group.attrs)
        if "RUN_CONFIG" not in _info.keys():
            raise HDFMappingError(
                device_name="bmotion",
                why=f"Missing 'RUN_CONFIG' attribute.",
            )
        for key in _info.keys():
            _info[key] = _bytes_to_str(_info[key])
        _info["RUN_CONFIG"] = toml.loads(_info["RUN_CONFIG"])
        self._run_config = _info.pop("RUN_CONFIG")
        _run_config = self._run_config  # type: dict

        # initialize motion group configs
        mg_configs = _run_config["run"]["motion_group"]
        n_mg_configs = len(mg_configs)
        if n_mg_configs == 0:
            raise HDFMappingError(
                device_name="bmotion",
                why=f"No motion groups exist in the configuration.",
            )
        for key, mg_config in mg_configs.items():
            name = self._generate_config_name(key, mg_config["name"])
            self.configs[name] = {**_info}
            self.configs[name]["MG_CONFIG"] = copy.deepcopy(mg_config)

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
                    "config column": "motion_group_id",
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
                "config column": "motion_group_id",
            }

        return state_key, state_entry

    @staticmethod
    def _generate_config_name(key, mg_name):
        """
        Generate the configuration name, which is a mash-up of the
        motion group key and name in the `bapsf_motion` run manager
        configuration.
        """
        return f"{key} - {mg_name}"

    @staticmethod
    def _split_config_name(config_name):
        """
        Splits a configuration name into its motion group key and name.
        """
        match = re.compile(r"\s*(?P<_id>[0-9]+)\s+(-)\s+(?P<mg_name>.+)").fullmatch(
            config_name
        )
        return (
            None
            if match is None
            else (match.group("_id").strip(), match.group("mg_name").strip())
        )

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
