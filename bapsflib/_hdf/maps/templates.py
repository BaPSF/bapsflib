"""
Module for the primary mapping template base class.
"""

__all__ = ["HDFMapTemplate", "MapTypes"]

import h5py
import os

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List


class MapTypes(Enum):
    """
    An enumeration of mapping types for unique elements of the HDF5 file
    to be mapped.
    """

    # todo: come up with at better name...this should really be types
    #       for the different HDF5 structural elements
    DIGITIZER = 1
    """Mapping class type for a digitized HDF5 file element."""

    CONTROL = 2
    """Mapping class type for a control device HDF5 file element."""

    MSI = 3
    """Mapping class type for a MSI diagnostic HDF5 file element."""


class HDFMapTemplate(ABC):
    """
    Template class for all mapping template classes.

    Note
    ----

    - To fully define a subclass the ``_build_configs`` abstract method
      needs to be defined.

      .. automethod:: _build_configs
         :noindex:

    - If a subclass needs to initialize additional variables before
      ``_build_configs`` is called in the ``__init__``, then those
      routines can be defined in the ``_init_before_build_configs``
      method.

      .. automethod:: _init_before_build_configs
         :noindex:

    """

    _maptype = NotImplemented  # type: MapTypes

    def __init__(self, group: h5py.Group):
        """
        Parameters
        ----------
        group : `h5py.Group`
            The HDF5 to apply the mapping to.
        """

        # condition group arg
        if isinstance(group, h5py.Group):
            self._group = group
        else:
            raise TypeError(
                "Argument `group` is not of type h5py.Group, got type "
                f"{type(group)} instead."
            )

        # define _info attribute
        self._info = {
            "group name": os.path.basename(group.name),
            "group path": group.name,
        }

        # initialize configuration dictionary
        self._configs = {}

        # initialize custom subclass items
        self._init_before_build_configs()

        # populate self.configs
        self._build_configs()

    @property
    def configs(self) -> Dict[str, Any]:
        """
        Dictionary containing all the relevant mapping information
        to translate the corresponding device data in the HDF5 file
        and provide a consistent user interface via
        `~bapsflib._hdf.utils.file.File`.
        """
        return self._configs

    @property
    def dataset_names(self) -> List[str]:
        """
        List of names of the HDF5 datasets within the mapped group, at
        the root level.
        """
        dnames = [
            name for name in self.group if isinstance(self.group[name], h5py.Dataset)
        ]
        return dnames

    @property
    def group_name(self) -> str:
        """Name of the mapped HDF5 group."""
        return self._info["group name"]

    @property
    def group_path(self) -> str:
        """Path of the mapped HDF5 group in the HDF5 file."""
        return self._info["group path"]

    @property
    def group(self) -> h5py.Group:
        """Instance of the HDF5 group that was mapped."""
        return self._group

    @property
    def info(self) -> Dict[str, Any]:
        """
        Metadata information about the mapping type and the mapped group
        location in the HDF5 file.

        Extended Summary
        ----------------
        The dictionary will contain the following elements:

        .. code-block:: python

            info = {
                "group name": "Device",  # name of the mapped HDF5 group
                "group path": "/foo/bar/Device", # internal HDF5 path to the group
                "maptype": self.maptype,  # mapping class type
            }

        """
        self._info["maptype"] = self.maptype
        return self._info

    @property
    def maptype(self) -> MapTypes:
        """Mapping class type (`MapTypes`)."""
        return self._maptype

    @property
    def subgroup_names(self) -> List[str]:
        """
        List of names of the HDF5 subgroups within the mapped group, at
        the root level.
        """
        sgroup_names = [
            name for name in self.group if isinstance(self.group[name], h5py.Group)
        ]
        return sgroup_names

    @abstractmethod
    def _build_configs(self):
        """
        Inspect the HDF5 group and build the configuration dictionary,
        :attr:`configs`.

        Functionality should specifically populate ``self._configs``
        instead of `self.configs`.  If a mapping fails, then a
        `~bapsflib.utils.exceptions.HDFMappingError` should be raised.
        """
        ...

    def _init_before_build_configs(self):
        """
        Any initialization that needs to be performed before executing
        ``self._build_configs`` in ``__init__``.

        By default we do nothing, but subclasses can override this for
        their specific purposes.
        """
        ...
