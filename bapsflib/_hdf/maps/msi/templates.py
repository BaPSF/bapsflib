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
"""Module for the template MSI mappers."""
__all__ = ["HDFMapMSITemplate"]

import h5py
import os

from abc import ABC, abstractmethod


class HDFMapMSITemplate(ABC):
    # noinspection PySingleQuotedDocstring
    '''
    Template class for all MSI diagnostic mapping classes to inherit
    from.

    Any inheriting class should define :code:`__init__` as::

        def __init__(self, group: h5py.Group):
            """
            :param group: HDF5 group object
            """
            # initialize
            HDFMapMSITemplate.__init__(self, group)

            # populate self.configs
            self._build_configs()

    .. note::

        Any method that raises a :exc:`NotImplementedError` is intended
        to be overwritten by the inheriting class.
    '''

    def __init__(self, group: h5py.Group):
        """
        :param group: the MSI diagnostic HDF5 group
        """
        # condition group arg
        if isinstance(group, h5py.Group):
            self._diag_group = group
        else:
            raise TypeError("arg `group` is not of type h5py.Group")

        # define info attribute
        self._info = {
            "group name": os.path.basename(group.name),
            "group path": group.name,
        }

        # initialize self.configs
        self._configs = {}

    @property
    def configs(self) -> dict:
        """
        Dictionary containing all the relevant mapping information to
        translate the HDF5 data into a numpy array.  The actually numpy
        array construction is done by
        :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`.

        **-- Constructing** :code:`configs` **--**

        The :code:`configs` dict is broken into a set of required keys
        (:code:`'shape'`, :code:`'shotnum'`, :code:`'signals'`, and
        :code:`'meta'`) and optional keys.  Any option key is considered
        as meta-info for the device and is added to the
        :attr:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI.info`
        dictionary when the numpy array is constructed.  The required
        keys constitute the mapping for constructing the numpy array.

        .. csv-table::
            :header: "Key", "Description"
            :widths: 20, 60

            "::

                configs['shape']
            ", "
            This is used as the :data:`shape` for the
            :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`
            constructed numpy array and typically looks like::

                configs['shape'] = (nsn, )

            where :code:`nsn` is the number of shot numbers saved to
            the diagnostic's datasets.
            "
            "::

                configs['shotnum']
            ", "
            Specifies the dataset(s) containing the recorded HDF5 shot
            numbers.  This maps to the :code:`'shotnum'` field of the
            numpy array constructed by
            :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`.  Should
            look like::

                configs['shotnum'] = {
                    'dset paths': ('/foo/bar/d1',),
                    'dset field': ('Shot number',),
                    'shape': (),
                    'dtype': numpy.int32,
                }

            where :code:`'dset paths'` is the internal HDF5 path to the
            dataset(s), :code:`'dset field'` is the field name of the
            dataset containing shot numbers, :code:`'shape'` of the shot
            number data, and :code:`'dtype'` is the numpy :code:`dtype`
            that the :code:`'shotnum'` field of the constructed numpy
            array will be.
            "
            "::

                configs['signals']
            ", "
            This is another dictionary where each key will map to a
            field in the
            :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI` numpy
            array.  For example, ::

                configs['signals'] = {
                    'current': {
                        'dset paths': ('/foo/bar/dset',),
                        'dset field': (),
                        'shape': (100,),
                        'dtype': numpy.float32},
                }

            would created a :code:`'current'` field in the constructed
            numpy array.  Any field specified in this key is considered
            to be your plot-able, or ""primary"", diagnostic data.
            "
            "::

                configs['meta']
            ", "
            This is another dictionary specifying meta-data that is both
            diagnostic and shot number specific.  For example, ::

                configs['meta'] = {
                    'shape': (),
                    'max current': {
                        'dset paths': ('/foo/bar/dset',),
                        'dset field': ('Max current',),
                        'shape': (),
                        'dtype': numpy.float32},
                }

            would create a :code:`'max current'` field in the
            :code:`'meta'` field of the constructed numpy array.
            "

        .. note::

            For further details, look to :ref:`add_msi_mod`.
        """
        return self._configs

    @property
    def info(self) -> dict:
        """
        MSI diagnostic dictionary of meta-info. For example, ::

            info = {
                'group name': 'Diagnostic',
                'group path': '/foo/bar/Diagnostic',
            }
        """
        return self._info

    @property
    def device_name(self) -> str:
        """Name of MSI diagnostic (device)"""
        return self._info["group name"]

    @property
    def group(self) -> h5py.Group:
        """Instance of MSI diagnostic group"""
        return self._diag_group

    @abstractmethod
    def _build_configs(self):
        """
        Gathers the necessary mapping data and constructs the
        :attr:`configs` dictionary.

        :raises: :exc:`NotImplementedError`

        .. note::

            Examine :meth:`_build_configs` in existing modules for ideas
            on how to override this method.  Also read
            :ref:`add_msi_mod`.
        """
        raise NotImplementedError
