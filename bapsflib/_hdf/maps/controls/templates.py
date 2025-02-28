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
__all__ = ["HDFMapControlTemplate", "HDFMapControlCLTemplate"]

import h5py
import numpy as np
import os

from abc import ABC, abstractmethod
from typing import Iterable, List, Tuple, Union
from warnings import warn

from bapsflib._hdf.maps.templates import HDFMapTemplate, MapTypes
from bapsflib._hdf.maps.controls.parsers import CLParse
from bapsflib._hdf.maps.controls.types import ConType
from bapsflib.utils.warnings import HDFMappingWarning


class HDFMapControlTemplate(HDFMapTemplate, ABC):
    """
    Template class for all control mapping classes to inherit from.

    .. note::

        If a control device is structured around a :ibf:`command list`,
        then its mapping class should subclass
        :class:`~.templates.HDFMapControlCLTemplate` instead.
    """
    _maptype = MapTypes.CONTROL
    _contype = NotImplemented  # type: ConType
    """
    Control device type.  (`ConType` `enum`)
    """

    def _init_before_build_configs(self):
        super()._init_before_build_configs()
        self._info["contype"] = self._contype

    @property
    def configs(self) -> dict:
        """
        Dictionary containing all the relevant mapping information to
        translate the HDF5 data into a numpy array by
        :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`.

        **-- Constructing** ``configs`` **--**

        The ``configs`` dict is a nested dictionary where the first
        level of keys represents the control device configuration names.
        Each configuration corresponds to one dataset in the HDF5
        control group and represents a grouping of state values
        associated with an probe or instrument used during an
        experiment.

        Each configuration is a dictionary consisting of a set of
        required keys (``'dset paths'``, ``'shotnum'``, and
        ``'state values'``) and optional keys.  Any optional key is
        considered as meta-info for the device and is added to the
        :attr:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls.info`
        dictionary when the numpy array is constructed.  The required
        keys constitute the mapping for constructing the numpy array
        and are explained in the table below.

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
            Defines how the run shot numbers are stored in the HDF5
            file, which are mapped to the ``'shotnum'`` field of the
            constructed numpy array.  Should look like, ::

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
            "
            "::

                config['state values']
            ", "
            This is another dictionary defining ``'state values'``.
            For example, ::

                config['state values'] = {
                    'xyz': {
                        'dset paths': config['dset paths'],
                        'dset field': ('x', 'y', 'z'),
                        'shape': (3,),
                        'dtype': numpy.float32}
                }

            will tell
            :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`
            to construct a numpy array with a the ``'xyz'`` field.
            This field would be a 3-element array of
            `numpy.float32`, where the ``'x'`` field of the
            HDF5 dataset is mapped to the 1st index, ``'y'`` is
            mapped to the 2nd index, and ``'z'`` is mapped to the
            3rd index.

            **Note:**

            * A state value field (key) can not be defined as
              ``'signal'`` since this field is reserved for digitizer
              data constructed by
              :class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`.
            * If state value data represents probe position data, then
              it should be given the field name (key) ``'xyz'``
              (like in the example above).

            "

        If a control device saves data around the concept of a
        :ibf:`command list`, then ``configs`` has a few additional
        required keys, see table below.

        .. csv-table:: Additional required keys for
                       ``config = configs['config name']`` when
                       the control device saves data around the concept
                       of a :ibf:`command list`.
            :header: "Key", "Description"
            :widths: 20, 60

            "::

                config['command list']
            ", "
            A tuple representing the original **command list**.
            For example, ::

                config['command list'] = ('VOLT: 20.0',
                                          'VOLT 25.0',
                                          'VOLT 30.0')

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
                        're pattern': re.compile(r'some RE pattern')}
                }

            where ``'re pattern'`` is the compiled RE pattern used
            to parse the original **command list**, ``'cl str'`` is
            the matched string segment of the **command list**, and
            ``'command list'`` is the set of values that will
            populate the constructed numpy array.
            "

        .. note::

            For further details, look to :ref:`add_control_mod`.
        """
        return self._configs

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
        Control device dictionary of meta-info. For example, ::

            info = {
                'group name': 'Control',
                'group path': '/foo/bar/Control',
                'contype': 'motion',
            }
        """
        return self._info

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
        return self._info["group name"]

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



class HDFMapControlCLTemplate(HDFMapControlTemplate):
    # noinspection PySingleQuotedDocstring
    """
    A modified :class:`HDFMapControlTemplate` template class for
    mapping control devices that record around the concept of a
    :ibf:`command list`.
    """

    def __init__(self, group: h5py.Group):
        """
        Parameters
        ----------
        group: `h5py.Group`
            the control device HDF5 group object

        Notes
        -----

        Any inheriting class should define ``__init__`` as::

            def __init__(self, group: h5py.Group):
                '''
                :param group: HDF5 group object
                '''
                # initialize
                HDFMapControlCLTemplate.__init__(self, control_group)

                # define control type
                self.info['contype'] = ConType.waveform

                # define known command list RE patterns
                self._default_re_patterns = (
                    r'(?P<FREQ>(\bFREQ\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))',
                )

                # populate self.configs
                self._build_configs()
        """
        HDFMapControlTemplate.__init__(self, group)

        # initialize internal 'command list' regular expression (RE)
        # patterns
        self._default_re_patterns = ()
        """tuple of default RE patterns for the control device"""

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
