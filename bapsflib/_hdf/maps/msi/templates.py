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

from bapsflib._hdf.maps.templates import HDFMapTemplate, MapTypes


class HDFMapMSITemplate(HDFMapTemplate, ABC):
    """
    Template class for all MSI diagnostic mapping classes to inherit
    from.
    """

    _maptype = MapTypes.MSI

    @property
    def configs(self) -> dict:
        """
        Dictionary containing all the relevant mapping information to
        translate the HDF5 data into a numpy array.  The actually numpy
        array construction is done by
        :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`.

        **-- Constructing** ``configs`` **--**

        The ``configs`` dict is broken into a set of required keys
        (``'shape'``, ``'shotnum'``, ``'signals'``, and ``'meta'``) and
        optional keys.  Any option key is considered as meta-info for
        the device and is added to the
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

            where ``nsn`` is the number of shot numbers saved to the
            diagnostic's datasets.
            "
            "::

                configs['shotnum']
            ", "
            Specifies the dataset(s) containing the recorded HDF5 shot
            numbers.  This maps to the ``'shotnum'`` field of the
            `numpy` array constructed by
            :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`.  Should
            look like::

                configs['shotnum'] = {
                    'dset paths': ('/foo/bar/d1',),
                    'dset field': ('Shot number',),
                    'shape': (),
                    'dtype': numpy.int32,
                }

            where ``'dset paths'`` is the internal HDF5 path to the
            dataset(s), ``'dset field'`` is the field name of the
            dataset containing shot numbers, ``'shape'`` of the shot
            number data, and ``'dtype'`` is the numpy `~numpy.dtype`
            that the ``'shotnum'`` field of the constructed numpy
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

            would create a ``'current'`` field in the constructed
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

            would create a ``'max current'`` field in the ``'meta'``
            field of the constructed numpy array.
            "

        .. note::

            For further details, look to :ref:`add_msi_mod`.
        """
        return super().configs

    @property
    def device_name(self) -> str:
        """Name of MSI diagnostic (device)"""
        return self.group_name
