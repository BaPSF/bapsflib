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
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

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

    @property
    def run_config_names(self):
        """
        Tuple of the bmotion run configuration names loaded and used
        during a data run.
        """
        return self._run_config_names

    def _init_before_build_configs(self):
        self._config_groups = []  # type: List[Group]
        self._run_config_names = tuple()  # type: Tuple[str]

    def _build_configs(self):
        # Build the attribute self.configs dictionary
        #
        self._verify_datasets()  # datasets must be verified before groups
        self._verify_groups()

        for group in self._config_groups:
            self._process_run_config_group(group)

        # rename configuration name to remain backwards compatible with version
        # v2025.3.0
        for name in list(self.configs.keys()):
            if len(self.configs[name]["meta"]) != 1:
                continue

            config = self.configs.pop(name)
            mg_id = config["meta"][0]["MG_ID"]
            config_name = self._generate_config_name(mg_id, name)
            self.configs[config_name] = config

        self._verify_multiple_run_config()

        if len(self.configs) == 0:
            raise HDFMappingError(
                device_name="bmotion",
                why="Unable to fully map any of the motion group configurations.",
            )

        # Build out each config
        for cname, _config in self.configs.items():  # type: str, dict
            mg_name = _config["meta"][0]["MG_CONFIG"]["name"]

            # for backwards compatibility, add keys to root level of the
            # configuration dictionary
            if len(_config["meta"]) == 1:
                for key in (
                    "BAPSFDAQ_MOTION_LV_VERSION",
                    "BAPSF_MOTION_VERSION",
                    "EXPANSION_ATTR",
                    "MG_CONFIG",
                ):
                    _config[key] = _config["meta"][0][key]

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
            ax_name_mapping = self._build_configs_get_axis_name_mapping(mg_name)
            if ax_name_mapping is None:
                continue

            # construct state values entry
            _config["state values"] = self._build_configs_construct_state_values_entry(
                ax_name_mapping
            )

            # update config
            self.configs[cname] = _config

        # check all configs define a 'state values' entry
        for cname in list(self.configs.keys()):
            if "state values" not in self.configs[cname]:
                del self.configs[cname]
        if len(self.configs) == 0:
            raise HDFMappingError(
                device_name="bmotion",
                why="Unable to fully map any of the motion group configurations.",
            )

        # define run_config_names
        names = []
        for items in self.configs.values():
            names.extend([meta_entry["RUN_CONFIG_NAME"] for meta_entry in items["meta"]])
        names = set(names)
        self._run_config_names = tuple(names)

    def _build_configs_get_axis_name_mapping(
        self, mg_name: str
    ) -> Union[List[Tuple[str, str]], None]:
        """
        Build mapping that connects dataset column name to the
        associated motion group axis name.
        """
        dset_axis_names = self._get_dataset(which="axis_names")
        indices = np.where(
            dset_axis_names["motion_group_name"] == bytes(mg_name, encoding="utf-8")
        )[0]
        if len(indices) == 0:
            warnings.warn(
                f"Unable to locate the '{mg_name}' configuration in the "
                f"'bmotion_axis_names' dataset.",
                HDFMappingWarning,
            )
            return None

        index = indices[0]
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
            return None

        return ax_name_mapping

    def _build_configs_construct_state_values_entry(
        self, ax_name_mapping: List[Tuple[str, str]]
    ) -> Dict[str, Any]:
        entry = dict()
        for col_name, ax_name in ax_name_mapping:
            # add "position" 'state values'
            dset = self.group[self.construct_dataset_name(which="positions")]
            _key, _entry = self._generate_state_entry(
                col_name=col_name,
                ax_name=ax_name,
                dset=dset,
                state_dict=entry,
            )
            entry[_key] = _entry

            # add "target_position" ' state values
            dset = self.group[self.construct_dataset_name(which="target_positions")]
            _key, _entry = self._generate_state_entry(
                col_name=col_name,
                ax_name=ax_name,
                dset=dset,
                state_dict=entry,
                ax_rename=lambda x: f"{x}_target",
            )
            entry[_key] = _entry
        return entry

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
                        f"Dataset {dset.name} does not have all required columns, "
                        f"missing columns: {column_names - set(dset.dtype.fields)}."
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
                why=f"Expected at least 1 sub-group, found NO groups.",
            )

        for ii, name in enumerate(group_names):
            group = self.group[name]
            if "RUN_CONFIG" not in group.attrs:
                continue

            self._config_groups.append(group)

        dset_runtime_list = self._get_dataset(which="main")  # Run-time list
        used_config_names = np.unique(dset_runtime_list["Configuration name"])
        used_config_names = [_bytes_to_str(name) for name in used_config_names]
        used_config_groups = []
        for group in self._config_groups:
            config_name = Path(group.name).stem
            if config_name in used_config_names:
                used_config_groups.append(group)
                continue

            warnings.warn(
                f"bmotion run configuration '{config_name}' was not "
                f"found in the 'Run time list' dataset.  Not including "
                f"configuration in the mapping.",
                HDFMappingWarning,
            )

        self._config_groups = used_config_groups

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
            name = self._generate_config_name(key=None, mg_name=mg_config["name"])

            entry = {
                **_info,
                "MG_ID": key,
                "MG_CONFIG": copy.deepcopy(mg_config),
                "RUN_CONFIG_NAME": Path(group.name).stem,
                "DRIVE_NAME": mg_config["drive"]["name"],
            }
            if name in self.configs:
                self.configs[name]["meta"] += (entry,)
            else:
                self.configs[name] = {}
                self.configs[name]["meta"] = (entry,)

    def _verify_multiple_run_config(self):
        if len(self._config_groups) == 1:
            return
        elif len(self._config_groups) == 0:  # coverage: ignore
            # keeping as a gatekeeper...this should never happen since
            # self._verify_groups() does this check
            raise HDFMappingError(
                device_name="bmotion",
                why="There are no valid configurations in the bmotion group.",
            )

        # If a motion group name is used in multiple run configurations,
        # then it must have the same bmotion_axis_names entries.  Otherwise,
        # these were two different probe drives with different run-time
        # states, which can NOT be handled by bapsflib at the moment.
        for config_name in list(self.configs.keys()):
            config_dict = self.configs[config_name]
            if len(config_dict["meta"]) == 0:  # coverage: ignore
                # this should never happen...keeping as a gatekeeper
                self.configs.pop(config_name)
                continue
            elif len(config_dict["meta"]) == 1:  # coverage: ignore
                continue

            # multiple run configurations were used for this motion group
            # must check that they have the same bmotion_axis_names entry

            self._verify_consistent_motion_group_run_time_state(config_name)

    def _verify_consistent_motion_group_run_time_state(self, config_name):
        # config_name is a configuration name in self.configs
        config_dict = self.configs[config_name]

        rtl_dset = self.group[self.construct_dataset_name(which="main")]
        ban_dset = self.group[self.construct_dataset_name(which="axis_names")]

        axis_names = {
            "a0": None,
            "a1": None,
            "a2": None,
            "a3": None,
            "a4": None,
            "a5": None,
        }  # type: Dict[str, Union[str, None]]
        remove_config = False
        for ii, entry in enumerate(list(config_dict["meta"])):
            run_config_name = entry["RUN_CONFIG_NAME"]
            mg_name = entry["MG_CONFIG"]["name"]

            # Note: self._verify_groups() checks that the run configuration
            #       name is present in the "Configuration name" column
            #       before allowing it to be mapped.
            rtl_mask = rtl_dset["Configuration name"] == run_config_name.encode("utf-8")
            shotnums = rtl_dset["Shot number"][rtl_mask]
            ban_shotnum = ban_dset["Shot number"]
            ban_shotnum_mask = np.zeros_like(ban_shotnum, dtype=bool)

            while True:
                invert_mask = np.logical_not(ban_shotnum_mask)
                indices = np.intersect1d(
                    shotnums,
                    ban_shotnum[invert_mask],
                    return_indices=True,
                )[2]

                if indices.size == 0:
                    break

                ban_shotnum_mask[np.where(invert_mask)[0][indices]] = True

                if np.all(ban_shotnum_mask):  # coverage: ignore
                    break

            mask_indices = ban_dset["motion_group_name"] == mg_name.encode("utf-8")
            mask = np.logical_and(ban_shotnum_mask, mask_indices)
            data_row = ban_dset[mask][0]
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

        if remove_config:
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
        return f"{mg_name}" if key is None else f"{key} - {mg_name}"

    @staticmethod
    def _split_config_name(config_name):
        """
        Splits a configuration name into its motion group key and name.
        """
        match = re.compile(r"\s*(?P<_id>[0-9]+)\s+(-)\s+(?P<mg_name>.+)").fullmatch(
            config_name
        )
        return (
            (None, config_name)
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

    def get_config_column_value(self, config_name: str) -> Union[str, None]:
        # bmotion uses the motion_group_name column as the configuration column,
        # so this method will return the motion group name or None
        config_name = self.process_config_name(config_name)
        _id, mg_name = self._split_config_name(config_name)
        return mg_name

    def get_config_name_by_drive_name(self, name: str) -> Union[str, None]:
        """
        Get the configuration name for the specified drive ``name``.
        """
        if not isinstance(name, str):
            raise TypeError(
                f"Argument 'name' must be of type str, got type {type(name)}."
            )

        config_name = None
        for _cname, config in self.configs.items():
            if name == config["meta"][0]["DRIVE_NAME"]:
                config_name = _cname
                break

        if config_name is None:
            raise ValueError(
                f"The given drive name '{name}' was not found among the "
                f"active bmotion configurations."
            )

        return config_name

    def get_config_name_by_motion_group_id(
        self, _id: Union[int, str]
    ) -> Union[str, None]:
        """
        Get the configuration name for the given motion group id.
        """
        if not isinstance(_id, (int, str)):
            raise TypeError(
                "The motion group id '_id' is supposed to be str or int, got "
                f"type {type(_id)} instead."
            )
        elif isinstance(_id, int):
            _id = f"{_id}"

        used_ids = []
        bad_ids = []
        id_config_names = []
        for _cname, config in self.configs.items():
            if len(config["meta"]) != 1:
                continue

            cid, mg_name = self._split_config_name(_cname)

            if cid is None:
                continue
            elif cid in bad_ids:
                continue
            elif cid in used_ids:
                ii = used_ids.index(cid)
                used_ids.pop(ii)
                id_config_names.pop(ii)
                bad_ids.append(cid)
            else:
                used_ids.append(cid)
                id_config_names.append(_cname)

        if len(used_ids) == 0 or _id not in used_ids:
            raise HDFMappingError(
                f"bmotion has multiple run configurations "
                f"({len(self._config_groups)}), so identifying a configuration "
                f"name by motion group ID is non-sensical.",
            )

        ii = used_ids.index(_id)
        return id_config_names[ii]

    def get_config_name_by_motion_group_name(self, name: str) -> Union[str, None]:
        """
        Get the configuration name for the given motion group name.
        """
        if not isinstance(name, str):
            raise TypeError("Expected 'name' to be str, got '{type(name)}' instead.")

        for _cname, config in self.configs.items():
            if name == _cname and name == config["meta"][0]["MG_CONFIG"]["name"]:
                return _cname

            if (
                len(config["meta"]) == 1
                and name == config["meta"][0]["MG_CONFIG"]["name"]
            ):
                return _cname

        raise ValueError(
            f"The given motion group name '{name}' was not found among the "
            f"mapped configurations.  Valid bmotion configurations are "
            f"{list(self.configs.keys())}."
        )

    def get_run_configuration(
        self, run_config_name: Optional[str] = None, as_toml_string: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        Get the TOML string associated with a specified bmotion run
        configuration, ``run_config_name``.

        Parameters
        ----------
        run_config_name : str, optional
            The name of the bmotion run configuration to retrieve.  If
            `None`, then the run configuration name will be inferred
            if only ONE configuration is present. (DEFAULT: `None`)

        as_toml_string : bool, optional
            If `True`, then return the configuration as a TOML string
            instead of a dictionary.  (DEFAULT: `False`)

        Returns
        -------
        Union[str, Dict[str, Any]]
            The TOML string or `dict` associated with the specified
            bmotion run configuration, ``run_config_name``.
        """
        if not isinstance(as_toml_string, bool):
            raise TypeError(
                f"Argument 'as_toml_string' must be of type bool, "
                f"got type {type(as_toml_string)}."
            )

        if run_config_name is not None and not isinstance(run_config_name, str):
            raise TypeError(
                "Argument 'run_config_name' must be of type str or None, "
                f"got type {type(run_config_name)}."
            )

        run_config_names = [Path(group.name).stem for group in self._config_groups]
        if run_config_name is None and len(self._config_groups) == 1:
            config_group = self._config_groups[0]
        elif run_config_name is None:
            raise ValueError(
                f"bmotion: bmotion has {len(self._config_groups)} run "
                f"configurations.  Set argument 'run_config_name' to one of "
                f"{run_config_names}."
            )
        elif run_config_name not in run_config_names:
            raise ValueError(
                f"bmotion: Argument run_config_name ('{run_config_name}') is "
                f"not among the existing run configurations, {run_config_names}."
            )
        else:
            config_group = None
            for group in self._config_groups:
                if Path(group.name).stem == run_config_name:
                    config_group = group
                    break

        if config_group is None:  # coverage: ignore
            # this should never happen...just putting this as a safeguard
            raise ValueError(
                "bmotion: Unable to find configuration group for run_config_name "
                f"'{run_config_name}'."
            )

        toml_string = _bytes_to_str(config_group.attrs["RUN_CONFIG"])

        if as_toml_string:
            return toml_string

        return toml.loads(toml_string)

    def process_config_name(self, config_name: Union[str, int]) -> Union[str, int]:
        if config_name in self.configs:
            return config_name

        # assume config_name is a probe drive name (e.g. Hera)
        nickname = config_name
        config_name = None
        drive_names = []
        for _config_name, config in self._configs.items():
            drive_name = config["meta"][0]["DRIVE_NAME"]
            drive_names.append(drive_name)
            if nickname == drive_name:
                config_name = _config_name

        if config_name is None:
            raise ValueError(
                "bmotion: Unable to process config_name.  No configuration name "
                f"'{nickname}' found in mapped configurations. Valid names "
                f"are {list(self.configs.keys())}."
            )

        if len(set(drive_names)) != len(drive_names):
            raise ValueError(
                "bmotion: Unable to process config_name.  The supplied nickname "
                f"'{nickname}' is used amongst multiple configurations.  Please "
                f"specify the exact configuration name.  Valid configuration "
                f"names are {list(self.configs.keys())}."
            )

        return config_name

    process_config_name.__doc__ = (
        HDFMapControlTemplate.process_config_name.__doc__
        + """
        Notes
        -----
        
        The bmotion mapping module `HDFMapControlBMotion` allows for drive 
        names to be used as configuration nicknames, as long as the drive is
        uniquely used amongst the deployed bmotion configurations.  This 
        allows a user to do something like 
        ``add_controls=[("bmotion", "Hades")]`` instead of 
        ``add_controls=[("bmotion", "<Hades> my_long_motion_list_name")]``
        when reading data with `~bapsflib._hdf.utils.file.File.read_data`.
        """
    )
