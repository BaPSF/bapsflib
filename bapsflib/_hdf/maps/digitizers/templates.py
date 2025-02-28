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
"""Module for the template digitizer mappers."""
__all__ = ["HDFMapDigiTemplate"]

import copy
import h5py

from abc import ABC, abstractmethod
from inspect import getdoc
from typing import Any, Dict, List, Tuple, Union
from warnings import warn

from bapsflib._hdf.maps.templates import HDFMapTemplate, MapTypes
from bapsflib.utils.warnings import HDFMappingWarning


class HDFMapDigiTemplate(HDFMapTemplate, ABC):
    """
    Template class for all digitizer mapping classes to inherit from.

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

    - Additionally, it is recommended to define additional helpers
      methods to construct and populate the :attr:`configs` dictionary.
      These would be utilized by ``_build_configs``.

      .. csv-table:: Possible helper methods.
          :header: "Method", "Description"
          :widths: 20, 60

          ":meth:`_adc_info_first_pass`", "
          Build the tuple of tuples containing the adc connected
          board and channels numbers, as well as, the associated
          setup configuration for each connected board.
          "
          ":meth:`_adc_info_second_pass`", "
          Review and update the adc tuple generated by
          :meth:`_adc_info_first_pass`.  Here, the expected
          datasets can be checked for existence and the setup
          dictionary can be append with any additional entries.
          "
          ":meth:`_find_active_adcs`", "
          Examine the configuration group to determine which
          digitizer adc's were used for the configuration.
          "
          ":meth:`_find_adc_connections`", "
          Used to determine the adc's connected board and
          channels.  It can also act as the seed for
          :meth:`_adc_info_first_pass`.
          "
          ":meth:`_parse_config_name`", "
          Parse the configuration group name to determine the
          digitizer configuration name.
          "
    """


    @property
    def active_configs(self) -> List[str]:
        """List of active digitizer configurations"""
        active = []
        for cname in self.configs:
            if self.configs[cname]["active"]:
                active.append(cname)

        return active

    @property
    def configs(self) -> dict:
        """
        Notes
        -----

        The information stored in this ``configs`` dictionary is used
        by `~bapsflib._hdf.utils.hdfreadmsi.HDFReadData` to build the
        `numpy` array from the associated HDF5 dataset(s).

        The ``configs`` `dict` is a nested dictionary where the first
        level of keys represents the digitizer configuration names.
        Each configuration name (`dict` key) has an associated `dict`
        value that consists of a set of polymorphic and non-polymorphic
        keys. Any additional keys are currently ignored.

        All the polymorphic and non-polymorphic keys described below
        are required keys.

        The non-polymorphic keys are as follows:

        .. csv-table:: Required Non-Polymorphic keys for
                       ``config=configs['config name']``
            :header: "Key", "Description"
            :widths: 20, 60

            "::

                config['active']
            ", "
            `True` or `False` indicating if this configuration was used
            in recording the digitizer datasets
            "
            "::

                config['adc']
            ", "
            Tuple of strings naming the adc's used for this
            configuration. For example, ::

                ('SIS 3301', )
            "
            "::

                config['config group path']
            ", "
            Internal HDF5 path to the digitizer configuration group.
            For example, ::

                '/foo/bar/SIS 3301/Configuration: first_run'
            "
            "::

                config['shotnum']
            ", "
            Dictionary defining how the digitzier shot numbers are
            recorded.  Assuming the shot numbers are recorded in the
            header dataset associated with the main dataset.  The
            dictionary should look like, ::

                config['shotnum'] = {
                    'dset field': ('Shot number',),
                    'shape': (),
                    'dtype': numpy.uint32,
                }

            where ``'dset field'`` is the field name of the
            header dataset containing shot numbers, ``'shape'`` is
            the `numpy` shape of the shot number data, and ``'dtype'``
            is the `numpy` `~numpy.dtype` of the data.  This all defines
            the `numpy` `~numpy.dtype` of the ``'shotnum'`` field in
            the
            :class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`
            constructed `numpy` array.
            "

        There is a required polymorphic key for each adc named in the
        ``configs['configs name']['adc']`` tuple.  This entry is a
        ``(N, 3)`` tuple where ``N`` is the number of DAQ boards
        associated with the `adc`.  Continuing with the example above,
        the first entry of the ``'SIS 3301'`` polymorphic key would
        look like::

        .. csv-table:: Breakdown of Polymorphic Key.
                       (``config=configs['config name']``)
            :header: "Key", "Description"
            :widths: 20, 60

            "::

                config['SIS 3301'][0][0]
            ", "
            `int` representing the connected board number
            "
            "::

                config['SIS 3301'][0][1]
            ", "
            ``Tuple[int, ...]`` representing the connected channel
            numbers associated with the board number
            "
            "::

                config['SIS 3301'][0][2]
            ", "
            ``Dict[str, Any]`` representing the setup configuration
            of the adc.  The dictionary should look like::

                config['SIS 3301'][0][2] = {
                    'bit: 10,
                    'clock rate':
                        astropy.units.Quantity(100.0, unit='MHz'),
                    'nshotnum': 10,
                    'nt': 10000,
                    'sample average (hardware)': None,
                    'shot average (software)': None,
                }

            where ``'bit'`` represents the bit resolution of the
            adc, ``'clock rate'`` represents the base clock rate of
            the adc, ``'nshotnum'`` is the number of shot numbers
            recorded, ``'nt'`` is the number of time samples
            recorded, ``'sample average (hardware)'`` is the number
            of time samples averaged together (this and the
            ``'clock rate'`` make up the ``'sample rate'``),
            and ``'shot average (software)'`` is the number of shot
            timeseries intended to be average together.
            "

        """
        return self._configs

    @abstractmethod
    def construct_dataset_name(
        self,
        board: int,
        channel: int,
        config_name: str = None,
        adc: str = None,
        return_info: bool = False,
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Constructs the name of the HDF5 dataset containing digitizer
        data.

        Parameters
        ----------
        board : `int`
            board number

        channel : `int`
            channel number

        config_name :  `str`, optional
            digitizer configuration name

        adc : `str`, optional
            analog-digital-converter name

        return_info : `bool`, optional
            `True` will return a dictionary of meta-info associated
            with the digitizer data (DEFAULT `False`)

        Returns
        -------
        Union[str, Tuple[str, Dict[str, Any]]]
            digitizer dataset name. If ``return_info=True``, then
            returns a tuple of (dataset name, dictionary of meta-info)

        Notes
        -----

        The returned adc information dictionary should look like::

            adc_dict = {
                'adc': str,
                'bit': int,
                'clock rate': astropy.units.Quantity,
                'configuration name': str,
                'digitizer': str,
                'nshotnum': int,
                'nt': int,
                'sample average (hardware)': int,
                'shot average (software)': int,
            }

        """
        ...

    @abstractmethod
    def construct_header_dataset_name(
        self,
        board: int,
        channel: int,
        config_name: str = None,
        adc: str = "",
        **kwargs,
    ) -> str:
        """
        Construct the name of the HDF5 header dataset associated with
        the digitizer dataset. The header dataset stores shot numbers
        and other shot number specific meta-data.  It also has a one-
        to-one row correspondence with the digitizer dataset.

        Parameters
        ----------
        board : `int`
            board number

        channel : `int`
            channel number

        config_name : `str`, optional
            digitizer configuration name

        adc : `str`, optional
            analog-digital-converter name

        Returns
        -------
        str
            header dataset name associated with the digitizer dataset
        """
        ...

    def deduce_config_active_status(self, config_name: str) -> bool:
        """
        Determines if data was recorded using the configuration
        specified by ``config_name``.  This is done by comparing
        the configuration name against the dataset names.

        Parameters
        ----------
        config_name : `str`
            digitizer configuration name

        Returns
        -------
        bool
            `True` if the configuration was used in recording the group
            datasets; otherwise, `False`

        .. note::

            If the digitizer does not use the configuration name in the
            name of the created datasets, then the subclassing digitizer
            mapping class should override this method with a rule that
            is appropriate for the digitizer the class is being
            designed for.
        """
        active = False

        # gather dataset names
        dataset_names = []
        for name in self.group:
            if isinstance(self.group[name], h5py.Dataset):
                dataset_names.append(name)

        # if config_name is in any dataset name then config_name is
        # active
        for name in dataset_names:
            if config_name in name:
                active = True
                break

        return active

    @property
    def device_adcs(self) -> Tuple[str, ...]:
        """
        Tuple of the analog-digital-convert (adc) names integrated into
        the digitizer.
        """
        return self._device_adcs

    @property
    def device_name(self) -> str:
        """Name of digitizer"""
        return self._info["group name"]

    def get_adc_info(
        self,
        board: int,
        channel: int,
        adc: str = None,
        config_name: str = None,
    ) -> Dict[str, Any]:
        """
        Get adc setup info dictionary associated with **board** and
        **channel**.

        Parameters
        ----------
        board : `int`
            board number

        channel : `int`
            channel number

        adc : `str`, optional
            analog-digital-converter name

        config_name : `str`, optional
            digitizer configuration name

        Returns
        -------
        Dict[str, Any]
            dictionary of adc setup info (bit, clock rate, averaging,
            etc.) associated with **board** and **channel**
        """
        # look for `config_name`
        if config_name is None:
            if len(self.active_configs) == 1:
                config_name = self.active_configs[0]
                warn(
                    f"`config_name` not specified, assuming '{config_name}'",
                    HDFMappingWarning,
                )
            else:
                raise ValueError("A valid `config_name` needs to be specified")
        elif self.configs[config_name]["active"] is False:
            warn(
                f"Digitizer configuration '{config_name}' is not actively used.",
                HDFMappingWarning,
            )

        # look for `adc`
        if adc is None:
            if len(self.configs[config_name]["adc"]) == 1:
                adc = self.configs[config_name]["adc"][0]
                warn(f"`adc` not specified, assuming '{adc}'", HDFMappingWarning)
            else:
                raise ValueError("A valid `adc` needs to be specified")

        # look for `board`
        adc_setup = self.configs[config_name][adc]
        found = False
        conn = (None, None, None)
        for conn in adc_setup:
            if board == conn[0]:
                found = True
                break
        if not found or not bool(board):
            raise ValueError(f"Board number ({board}) not found in setup")

        # look for `channel`
        if channel not in conn[1] or not bool(channel):
            raise ValueError(f"Channel number ({channel})  not found in setup")

        # get dictionary and add keys
        # - 'board', 'channel', 'adc', 'digitizer', and
        #   'configuration name'
        adc_info = copy.deepcopy(conn[2])
        adc_info["adc"] = adc
        adc_info["board"] = board
        adc_info["channel"] = channel
        adc_info["configuration name"] = config_name
        adc_info["digitizer"] = self.device_name

        return adc_info


