"""
Module for the "bmotion" motion control mapper
`~bapsflib._hdf.maps.controls.phys180e.HDFMapControlPositions180E`.
"""

__all__ = ["HDFMapControlPositions180E"]

import numpy as np

from bapsflib._hdf.maps.controls.templates import HDFMapControlTemplate
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib.utils import _bytes_to_str
from bapsflib.utils.exceptions import HDFMappingError


class HDFMapControlPositions180E(HDFMapControlTemplate):
    """
    Mapping module for the control device '180E_positions'.

    Simple group structure looks like:

    .. code-block:: none

        +-- Positions
        |   +-- positions_setup_array       [Dataset]

    """

    _contype = ConType.MOTION
    _required_dataset_names = {
        "main": "positions_setup_array",
    }
    _EXPECTED_GROUP_NAME = "Positions"

    @property
    def device_name(self) -> str:
        return "180E_positions"

    @property
    def one_config_per_dset(self) -> bool:
        # There is always just one dataset and just one run configuration
        return True

    def construct_dataset_name(self, *args) -> str:
        # There is only every one dataset name
        return self._required_dataset_names["main"]

    def _init_before_build_configs(self): ...

    def _build_configs(self):
        # Build the attribute self.configs dictionary
        #
        self._verify_datasets()  # datasets must be verified before groups
        self._verify_groups()

        dset_path = f"{self.group_path}/{self._required_dataset_names['main']}"
        _config = {
            "dset paths": (dset_path,),
            "shotnum": {
                "dset paths": (dset_path,),
                "dset field": ("Line_number",),
                "shape": (),
                "dtype": np.int32,
            },
            "state values": {
                "xyz": {
                    "dset paths": (dset_path,),
                    "dset field": ("x", "y", ""),
                    "shape": (3,),
                    "dtype": np.float64,
                    "config column": None,
                },
            },
        }
        self._configs["positions"] = _config

    def _verify_datasets(self):
        # 180E_positions group contains 1 datasets
        # - "positions_setup_array" <dataset>
        #
        # verify datasets existence
        dataset_names = set(self.dataset_names)
        required_datasets = set(self._required_dataset_names.values())
        _remainder_dsets = required_datasets - dataset_names
        if len(_remainder_dsets) != 0:
            raise HDFMappingError(
                device_name=self.device_name,
                why=f"Missing datasets {_remainder_dsets}.",
            )
        if len(dataset_names) != 1:
            raise HDFMappingError(
                device_name=self.device_name,
                why=f"Expected 1 dataset, found {len(dataset_names)} datasets.",
            )

        # verify dataset structure
        dset_name = list(dataset_names)[0]
        dset = self.group[dset_name]
        if dset.dtype.fields is None:
            raise HDFMappingError(
                device_name=self.device_name,
                why=f"Dataset {dset.name} does not have ANY named columns.",
            )

        column_names = {"Line_number", "x", "y"}
        if len(column_names - set(dset.dtype.fields)) != 0:
            raise HDFMappingError(
                device_name=self.device_name,
                why=(
                    f"Dataset {dset.name} does NOT have all required columns, "
                    f"missing columns: {column_names - set(dset.dtype.fields)}."
                ),
            )

    def _verify_groups(self):
        # 180E_positions group contains 0 group
        #
        group_names = self.subgroup_names
        if len(group_names) != 0:
            raise HDFMappingError(
                device_name=self.device_name,
                why=f"Expected NO sub-groups, found {len(group_names)} groups.",
            )
