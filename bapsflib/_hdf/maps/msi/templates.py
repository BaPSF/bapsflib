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

from abc import ABC
from inspect import getdoc

from bapsflib._hdf.maps.templates import HDFMapTemplate, MapTypes


class HDFMapMSITemplate(HDFMapTemplate, ABC):
    """
    Template class for all MSI diagnostic mapping classes to inherit
    from.

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

    _maptype = MapTypes.MSI

    @property
    def configs(self) -> dict:
        """
        Notes
        -----

        The information stored in this ``configs`` dictionary is used
        by `~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI` to build the MSI
        `numpy` array from the associated HDF5 dataset(s).

        The ``configs`` dict is broken into a set of required keys
        (``'shape'``, ``'shotnum'``, ``'signals'``, and ``'meta'``) and
        optional keys.  The required keys are used by
        `~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI` to extract the MSI
        data and build the `numpy` arrays.  Any optional key is
        considered as meta-data and is included in the
        :attr:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI.info`
        attribute of the constructed MSI `numpy` array.

        .. csv-table::
            :header: "Key", "Description"
            :widths: 20, 60

            "::

                configs['shape']
            ", "
            This is used as the ``shape`` for the
            `~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`
            constructed `numpy` array and typically looks like::

                configs['shape'] = (nsn, )

            where ``nsn`` is the number of shot numbers saved to the
            diagnostics's datasets.
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
            number data, and ``'dtype'`` is the `numpy` `~numpy.dtype`
            that the ``'shotnum'`` field of the constructed `numpy`
            array will be.
            "
            "::

                configs['signals']
            ", "
            A dictionary that maps MSI data signals to the `numpy` array
            constructed by
            :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`.  Each
            key in this dictionary corresponds to a field name in
            :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI` array
            and the value defines the data location in the HDF5 file.
            For example, ::

                configs['signals'] = {
                    'current': {
                        'dset paths': ('/foo/bar/dset',),
                        'dset field': (),
                        'shape': (100,),
                        'dtype': numpy.float32,
                    },
                }

            would create a ``'current'`` field in the constructed
            `numpy` array.  Any field specified in this key is considered
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
            field of the constructed `numpy` array.
            "

        .. note::

            For further details, look to :ref:`add_msi_mod`.
        """
        return super().configs

    @property
    def device_name(self) -> str:
        """Name of MSI diagnostic (device)"""
        return self.group_name


HDFMapMSITemplate.configs.__doc__ = (
    getdoc(HDFMapTemplate.configs) + "\n\n" + getdoc(HDFMapMSITemplate.configs)
)
