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
from typing import Iterable, List, Union
from warnings import warn

from bapsflib._hdf.maps.controls.parsers import CLParse
from bapsflib._hdf.maps.controls.types import ConType


class HDFMapControlTemplate(ABC):
    # noinspection PySingleQuotedDocstring
    '''
    Template class for all control mapping classes to inherit from.

    Any inheriting class should define :code:`__init__` as::

        def __init__(self, group: h5py.Group):
            """
            :param group: HDF5 group object
            """
            # initialize
            HDFMapControlTemplate.__init__(self, group)

            # define control type
            self.info['contype'] = ConType.motion

            # populate self.configs
            self._build_configs()

    .. note::

        * Any method that raises a :exc:`NotImplementedError` is
          intended to be overwritten by the inheriting class.
        * :code:`from bapsflib._hdf.maps.controls import ConType`
        * If a control device is structured around a
          :ibf:`command list`, then its mapping class should subclass
          :class:`~.templates.HDFMapControlCLTemplate`.
          Which is a subclass of
          :class:`~.templates.HDFMapControlTemplate`,
          but adds methods for parsing/handling a command list.
    '''

    def __init__(self, group: h5py.Group):
        """
        :param group: the control device HDF5 group object
        """
        # condition group arg
        if isinstance(group, h5py.Group):
            self._control_group = group
        else:
            raise TypeError("arg `group` is not of type h5py.Group")

        # define _info attribute
        self._info = {
            "group name": os.path.basename(group.name),
            "group path": group.name,
            "contype": NotImplemented,
        }

        # initialize configuration dictionary
        self._configs = {}

    @property
    def configs(self) -> dict:
        """
        Dictionary containing all the relevant mapping information to
        translate the HDF5 data into a numpy array by
        :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`.

        **-- Constructing** :code:`configs` **--**

        The :code:`configs` dict is a nested dictionary where the first
        level of keys represents the control device configuration names.
        Each configuration corresponds to one dataset in the HDF5
        control group and represents a grouping of state values
        associated with an probe or instrument used during an
        experiment.

        Each configuration is a dictionary consisting of a set of
        required keys (:code:`'dset paths'`, :code:`'shotnum'`, and
        :code:`'state values'`) and optional keys.  Any optional key is
        considered as meta-info for the device and is added to the
        :attr:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls.info`
        dictionary when the numpy array is constructed.  The required
        keys constitute the mapping for constructing the numpy array
        and are explained in the table below.

        .. csv-table:: Dictionary breakdown for
                       :code:`config = configs['config name']`
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
            file, which are mapped to the :code:`'shotnum'` field of the
            constructed numpy array.  Should look like, ::

                config['shotnum'] = {
                    'dset paths': config['dset paths'],
                    'dset field': ('Shot number',),
                    'shape': (),
                    'dtype': numpy.int32,
                }

            where :code:`'dset paths'` is the internal HDF5 path to the
            dataset, :code:`'dset field'` is the field name of the
            dataset containing shot numbers, :code:`'shape'` is the
            numpy shape of the shot number data, and :code:`'dtype'`
            is the numpy :code:`dtype` of the data.  This all defines
            the numpy :code:`dtype` of the :code:`'shotnum'` field in
            the
            :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`
            constructed numpy array.
            "
            "::

                config['state values']
            ", "
            This is another dictionary defining :code:`'state values`.
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
            to construct a numpy array with a the :code:`'xyz'` field.
            This field would be a 3-element array of
            :code:`numpy.float32`, where the :code:`'x'` field of the
            HDF5 dataset is mapped to the 1st index, :code:`'y'` is
            mapped to the 2nd index, and :code:`'z'` is mapped to the
            3rd index.

            **Note:**

            * A state value field (key) can not be defined as
              :code:`'signal'` since this field is reserved for
              digitizer data constructed by
              :class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`.
            * If state value data represents probe position data, then
              it should be given the field name (key) :code:`'xyz'`
              (like in the example above).

            "

        If a control device saves data around the concept of a
        :ibf:`command list`, then :code:`configs` has a few additional
        required keys, see table below.

        .. csv-table:: Additional required keys for
                       :code:`config = configs['config name']` when
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
            :code:`'command list'`, :code:`'cl str`,
            and :code:`'re pattern'`.
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

            where :code:`'re pattern'` is the compiled RE pattern used
            to parse the original **command list**, :code:`'cl str'` is
            the matched string segment of the **command list**, and
            :code:`'command list'` is the set of values that will
            populate the constructed numpy array.
            "

        .. note::

            For further details, look to :ref:`add_control_mod`.
        """
        return self._configs

    @property
    def contype(self) -> ConType:
        """control device type"""
        return self._info["contype"]

    @property
    def dataset_names(self) -> List[str]:
        """list of names of the HDF5 datasets in the control group"""
        dnames = [
            name for name in self.group if isinstance(self.group[name], h5py.Dataset)
        ]
        return dnames

    @property
    def group(self) -> h5py.Group:
        """Instance of the HDF5 Control Device group"""
        return self._control_group

    @property
    def has_command_list(self) -> bool:
        """
        :return: :code:`True` if dataset utilizes a command list
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
        :code:`'True'` if each control configuration has its own dataset
        """
        n_dset = len(self.dataset_names)
        n_configs = len(self._configs)
        return True if n_dset == n_configs else False

    @property
    def subgroup_names(self) -> List[str]:
        """list of names of the HDF5 sub-groups in the control group"""
        sgroup_names = [
            name for name in self.group if isinstance(self.group[name], h5py.Group)
        ]
        return sgroup_names

    @property
    def device_name(self) -> str:
        """Name of Control device"""
        return self._info["group name"]

    @abstractmethod
    def construct_dataset_name(self, *args) -> str:
        """
        Constructs the dataset name corresponding to the input
        arguments.

        :return: name of dataset
        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError

    @abstractmethod
    def _build_configs(self):
        """
        Gathers the necessary metadata and fills :data:`configs`.

        :raise: :exc:`NotImplementedError`
        """
        raise NotImplementedError


class HDFMapControlCLTemplate(HDFMapControlTemplate):
    # noinspection PySingleQuotedDocstring
    '''
    A modified :class:`HDFMapControlTemplate` template class for
    mapping control devices that record around the concept of a
    :ibf:`command list`.

    Any inheriting class should define :code:`__init__` as::

        def __init__(self, group: h5py.Group):
            """
            :param group: HDF5 group object
            """
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

    .. note::

        * Any method that raises a :exc:`NotImplementedError` is
          intended to be overwritten by the inheriting class.
        * :code:`from bapsflib._hdf.maps.controls import ConType`
    '''

    def __init__(self, group: h5py.Group):
        """
        :param group: the control device HDF5 group object
        """
        HDFMapControlTemplate.__init__(self, group)

        # initialize internal 'command list' regular expression (RE)
        # patterns
        self._default_re_patterns = ()
        """tuple of default RE patterns for the control device"""

    @abstractmethod
    def _default_state_values_dict(self, config_name: str) -> dict:
        """
        Returns the default :code:`'state values'` dictionary for
        configuration *config_name*.

        :param str config_name: configuration name
        :raise: :exc:`NotImplementedError`

        :Example:

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
        raise NotImplementedError

    def _construct_state_values_dict(
        self, config_name: str, patterns: Union[str, Iterable[str]]
    ) -> dict:
        """
        Returns a dictionary for
        :code:`configs[config_name]['state values']` based on the
        supplied RE patterns. :code:`None` is returned if the
        construction failed.

        :param config_name: configuration name
        :param patterns: list of RE pattern strings
        """
        # -- check requirements exist before continuing             ----
        # get dataset
        dset_path = self._configs[config_name]["dset paths"][0]
        dset = self.group.get(dset_path)

        # ensure 'Command index' is a field
        if "Command index" not in dset.dtype.names:
            warn(f"Dataset '{dset_path}' does NOT have 'Command index' field")
            return {}

        # ensure 'Command index' is a field of scalars
        if dset.dtype["Command index"].shape != () or not np.issubdtype(
            dset.dtype["Command index"].type, np.integer
        ):
            warn(
                f"Dataset '{dset_path}' 'Command index' field is NOT a column of integers"
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
        for `config_name`.

        :param str config_name: configuration name
        """
        # retrieve command list
        cl = self._configs[config_name]["command list"]

        # define clparse and return
        return CLParse(cl)

    def reset_state_values_config(self, config_name: str, apply_patterns=False):
        """
        Reset the :code:`configs[config_name]['state values']`
        dictionary.

        :param config_name: configuration name
        :param bool apply_patterns: Set :code:`False` (DEFAULT) to
            reset to :code:`_default_state_values_dict(config_name)`.
            Set :code:`True` to rebuild dict using
            :attr:`_default_re_patterns`.
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
        Rebuild and set
        :code:`configs[config_name]['state values']` based on the
        supplied RE *patterns*.

        :param config_name: configuration name
        :param patterns: list of RE strings
        """
        # construct dict for 'state values' dict
        sv_dict = self._construct_state_values_dict(config_name, patterns)

        # update 'state values' dict
        if not bool(sv_dict):
            # do nothing since default parsing was unsuccessful
            warn("RE parsing of 'command list' was unsuccessful, doing nothing")
        else:
            self._configs[config_name]["state values"] = sv_dict
