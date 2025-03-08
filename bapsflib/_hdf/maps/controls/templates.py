# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2018 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
"""Module for the template control mappers."""
__all__ = [
    "ControlMap",
    "HDFMapControlTemplate",
    "HDFMapControlCLTemplate",
]

import numpy as np

from abc import ABC, abstractmethod
from inspect import getdoc
from typing import Iterable, Tuple, Union
from warnings import warn

from bapsflib._hdf.maps.controls.parsers import CLParse
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib._hdf.maps.templates import HDFMapTemplate, MapTypes
from bapsflib.utils.warnings import HDFMappingWarning

# define type aliases
ControlMap = Union["HDFMapControlTemplate", "HDFMapControlCLTemplate"]


class HDFMapControlTemplate(HDFMapTemplate, ABC):
    """
    Template class for all control mapping classes to inherit from.

    Note
    ----

    - If a control device is structured around a :ibf:`command list`,
      then its mapping class should subclass
      :class:`~.templates.HDFMapControlCLTemplate` instead.

    - To fully define a subclass there are several abstract methods that
      need to be defined, which includes

      - :meth:`construct_dataset_name`
      - :meth:`_build_configs`

        .. automethod:: _build_configs

    - If a subclass needs to initialize additional variables before
      ``_build_configs`` is called in the ``__init__``, then those
      routines can be defined in the ``_init_before_build_configs``
      method.

      .. automethod:: _init_before_build_configs
         :noindex:

    """

    _maptype = MapTypes.CONTROL
    _contype = NotImplemented  # type: ConType
    """
    Control device type.  (`ConType` `enum`)
    """

    @property
    def configs(self) -> dict:
        """
        Notes
        -----

        The information stored in the ``configs`` dictionary is used by
        `~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls` to build
        the `numpy` data array from the associated HDF5 dataset(s).

        The ``configs`` `dict` is a nested dictionary where the first
        level of keys represents the control device configuration
        names.  Each configuration name (`dict` key) has an associated
        `dict` value that consists of a set of required keys and
        optional keys.  Any optional key is considered as meta-info for
        the device and is added to the
        :attr:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls.info`
        dictionary.

        The required keys are as follows:

        .. csv-table:: Dictionary breakdown for
                       ``config = configs['config name']``
            :header: "Key", "Description"
            :widths: 20, 60

            "::

                config['dset paths']
            ", "
            Internal HDF5 path to the dataset associated with the
            control device configuration. For example, ::

                config['dset paths'] = ('/foo/bar/Control/d1', )

            "
            "::

                config['shotnum']
            ", "
            Defines how the run shot numbers are stored in the
            associated HDF5 dataset, which are mapped to the
            ``'shotnum'`` field of the constructed `numpy` array.
            Should look like, ::

                config['shotnum'] = {
                    'dset paths': config['dset paths'],
                    'dset field': ('Shot number',),
                    'shape': (),
                    'dtype': numpy.int32,
                }

            where ``'dset paths'`` is the internal HDF5 path to the
            dataset, ``'dset field'`` is the field name of the
            dataset containing shot numbers, ``'shape'`` is the
            numpy shape of the shot number data, and ``'dtype'``
            is the numpy `~numpy.dtype` of the data.  This all defines
            the numpy `~numpy.dtype` of the ``'shotnum'`` field in
            the
            :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`
            constructed numpy array.

            If the ``'dset paths'`` entry is defined as `None`, then
            the `bapsflib` routines will default to the ``'dset paths'``
            defined for each of the ``'state values'`` entries.
            "
            "::

                config['state values']
            ", "
            This is another dictionary defining ``'state values'``.
            For example,::

                config['state values'] = {
                    'xyz': {
                        'dset paths': config['dset paths'],
                        'dset field': ('x', 'y', 'z'),
                        'shape': (3,),
                        'dtype': numpy.float32,
                        'config column': 'Configuration name',
                    },
                }

            will tell
            :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`
            to construct a numpy array with a ``'xyz'`` field.
            This field would be a 3-element array of
            `numpy.float32`, where the ``'x'`` field of the
            HDF5 dataset is mapped to the 1st index, ``'y'`` is
            mapped to the 2nd index, and ``'z'`` is mapped to the
            3rd index.

            The ``'config column'`` indicates the dataset column name
            that holds the configuration identification value (name,
            id, etc.).  This field is optional, and will look for the
            column with 'configuration' in its name if the field is
            omitted.

            **Note:**

            * A state value field (key) can not be defined as
              ``'signal'`` since this field is reserved for digitizer
              data constructed by
              :class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`.
            * If state value data represents probe position data, then
              it should be given the field name (key) ``'xyz'``
              (like in the example above).

            "

        """
        return super().configs

    @property
    def contype(self) -> ConType:
        """Control device type."""
        return self._contype

    @property
    def has_command_list(self) -> bool:
        """
        ``True`` if the control device utilizes a command list
        """
        has_cl = False
        for config_name in self._configs:
            if "command list" in self._configs[config_name]:
                has_cl = True
                break
        return has_cl

    @property
    def info(self) -> dict:
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
                "contype": self.contype,  # control device type
            }

        """
        self._info["contype"] = self.contype
        return super().info

    @property
    def one_config_per_dset(self) -> bool:
        """
        `True` if each control configuration has its own dataset
        """
        n_dset = len(self.dataset_names)
        n_configs = len(self._configs)
        return True if n_dset == n_configs else False

    @property
    def device_name(self) -> str:
        """Name of Control device"""
        return self.group_name

    def get_config_id(self, config_name: str) -> str:
        """
        Get the configuration identifier for the given ``config_name``.
        This identifier is the string value used in the HDF5 datasets.

        Parameters
        ----------
        config_name : `str`
            The configuration name used in :attr:`configs`.
        """
        return config_name

    @abstractmethod
    def construct_dataset_name(self, *args) -> str:
        """
        Constructs the dataset name corresponding to the input
        arguments.

        Returns
        -------
        str
            name of dataset
        """
        ...


HDFMapControlTemplate.configs.__doc__ = (
    getdoc(HDFMapTemplate.configs) + "\n\n" + getdoc(HDFMapControlTemplate.configs)
)


class HDFMapControlCLTemplate(HDFMapControlTemplate, ABC):
    """
    A modified :class:`HDFMapControlTemplate` template class for
    mapping control devices that record data around the concept of a
    :ibf:`command list`.

    Note
    ----

    - If the control device is NOT structured around a
      :ibf:`command list`, then its mapping class should subclass
      :class:`~.templates.HDFMapControlTemplate` instead.

    - To fully define a subclass there are several abstract methods that
      need to be defined, which includes

      - :meth:`construct_dataset_name`
      - :meth:`_build_configs`
      - :meth:`_default_state_values_dict`

        .. automethod:: _build_configs
        .. automethod:: _default_state_values_dict

    - If a subclass needs to initialize additional variables before
      ``_build_configs`` is called in the ``__init__``, then those
      routines can be defined in the ``_init_before_build_configs``
      method.

      .. automethod:: _init_before_build_configs
         :noindex:

    """

    _default_re_patterns = ()  # type: Tuple[str, ...]
    """Tuple of RE pattern strings for the control device."""

    @abstractmethod
    def _default_state_values_dict(self, config_name: str) -> dict:
        """
        Returns the default ``'state values'`` dictionary for
        configuration *config_name*.

        Parameters
        ----------
        config_name: `str`
            configuration name

        Examples
        --------

        .. code-block:: python

            # define default dict
            default_dict = {
                'command': {
                    'dset paths':
                        self._configs[config_name]['dese paths'],
                    'dset field': ('Command index', ),
                    're pattern': None,
                    'command list':
                        self._configs[config_name]['command list'],
                    'cl str':
                        self._configs[config_name]['command list'],
                    'shape': (),
                }
            }
            default_dict['command']['dtype'] = \\
                default_dict['command']['command list'].dtype

            # return
            return default_dict

        """
        ...

    def _construct_state_values_dict(
        self, config_name: str, patterns: Union[str, Iterable[str]]
    ) -> dict:
        """
        Returns a dictionary for
        ``configs[config_name]['state values']`` based on the
        supplied RE patterns. `None` is returned if the
        construction failed.

        Parameters
        ----------
        config_name : `str`
            configuration name

        patterns : `Union[str, Iterable[str]]
            list of RE pattern strings
        """
        # -- check requirements exist before continuing             ----
        # get dataset
        dset_path = self._configs[config_name]["dset paths"][0]
        dset = self.group.get(dset_path)

        # ensure 'Command index' is a field
        if "Command index" not in dset.dtype.names:
            warn(
                f"Dataset '{dset_path}' does NOT have 'Command index' field",
                HDFMappingWarning,
            )
            return {}

        # ensure 'Command index' is a field of scalars
        if dset.dtype["Command index"].shape != () or not np.issubdtype(
            dset.dtype["Command index"].type, np.integer
        ):
            warn(
                f"Dataset '{dset_path}' 'Command index' field is NOT a column "
                f"of integers",
                HDFMappingWarning,
            )
            return {}

        # -- apply RE patterns to 'command list'                    ----
        success, sv_dict = self.clparse(config_name).apply_patterns(patterns)

        # regex was unsuccessful, return alt_dict
        if not success:
            return {}

        # -- complete `sv_dict` before return                       ----
        # 1. 'command list' and 'cl str' are tuples from clparse
        # 2. add 'dset paths'
        # 3. add 'dset field'
        # 4. add 'shape'
        # 5. 'dtype' defined by clparse.apply_patterns
        #
        for state in sv_dict:
            # add additional keys
            sv_dict[state]["dset paths"] = self._configs[config_name]["dset paths"]
            sv_dict[state]["dset field"] = ("Command index",)
            sv_dict[state]["shape"] = ()

        # return
        return sv_dict

    @property
    def configs(self) -> dict:
        """
        Notes
        -----

        When a control device saves around the concept of a
        :ibf:`command list`, then ``configs`` shares the same structure
        as the `HDFMapControlTemplate` `~HDFMapControlTemplate.configs`
        ...with a couple alterations.  There is now a required
        ``'command list'`` key, and the ``'state values'`` needs
        additional information.

        The modified required keys look like:

        .. csv-table:: Additional :ibf:`command list` required keys for
                       ``config = configs['config name']``
            :header: "Key", "Description"
            :widths: 20, 60

            "::

                config['command list']
            ", "
            A `tuple` representing the original **command list**.
            For example, ::

                config['command list'] = (
                    'VOLT: 20.0',
                    'VOLT 25.0',
                    'VOLT 30.0',
                )

            "
            "::

                config['state values']
            ", "
            Has all the same keys as before, plus the addition of
            ``'command list'``, ``'cl str'``, and ``re pattern``.
            For example, ::

                config['state values'] = {
                    'command': {
                        'dset paths': config['dset paths'],
                        'dset field': ('Command index',),
                        'shape': (),
                        'dtype': numpy.float32,
                        'command list': (20.0, 25.0, 30.0),
                        'cl str': ('VOLT: 20.0', 'VOLT 25.0',
                                   'VOLT 30.0'),
                        're pattern': re.compile(r'some RE pattern'),
                    },
                }

            where ``'re pattern'`` is the compiled RE pattern used
            to parse the original **command list**, ``'cl str'`` is
            the matched string segment of the **command list**, and
            ``'command list'`` is the set of values that will
            populate the constructed numpy array.
            "
        """
        return super().configs

    def clparse(self, config_name: str) -> CLParse:
        """
        Return instance of
        :class:`~bapsflib.lapd.controls.parsers.CLParse`
        for ``config_name``.

        Parameters
        ----------
        config_name : `str`
            configuration name
        """
        # retrieve command list
        cl = self._configs[config_name]["command list"]

        # define clparse and return
        return CLParse(cl)

    def reset_state_values_config(self, config_name: str, apply_patterns=False):
        """
        Reset the ``configs[config_name]['state values']`` dictionary.

        Parameters
        ----------
        config_name : `str`
            configuration name

        apply_patterns : `bool`
            Set `False` (DEFAULT) to reset to
            ``_default_state_values_dict(config_name)``.  Set `True` to
            rebuild dict using :attr:`_default_re_patterns`.
        """
        if apply_patterns:
            # get sv_dict dict
            sv_dict = self._construct_state_values_dict(
                config_name, self._default_re_patterns
            )
            if not bool(sv_dict):
                sv_dict = self._default_state_values_dict(config_name)
        else:
            # get default dict
            sv_dict = self._default_state_values_dict(config_name)

        # reset config
        self._configs[config_name]["state values"] = sv_dict

    def set_state_values_config(
        self, config_name: str, patterns: Union[str, Iterable[str]]
    ):
        """
        Rebuild and set ``configs[config_name]['state values']`` based
        on the supplied RE *patterns*.

        Parameters
        ----------
        config_name : `str`
            configuration name

        patterns : `Union[str, Iterable[str]]`
            list of RE strings
        """
        # construct dict for 'state values' dict
        sv_dict = self._construct_state_values_dict(config_name, patterns)

        # update 'state values' dict
        if not bool(sv_dict):
            # do nothing since default parsing was unsuccessful
            warn(
                "RE parsing of 'command list' was unsuccessful, doing nothing",
                HDFMappingWarning,
            )
        else:
            self._configs[config_name]["state values"] = sv_dict


HDFMapControlCLTemplate.configs.__doc__ = (
    getdoc(HDFMapTemplate.configs) + "\n\n" + getdoc(HDFMapControlCLTemplate.configs)
)
