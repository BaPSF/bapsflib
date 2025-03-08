.. _hdfmap_details:

HDF5 File Mapping (:class:`~bapsflib._hdf.maps.mapper.HDFMapper`)
=================================================================

.. contents:: Contents
    :depth: 3
    :local:

:class:`~bapsflib._hdf.map.mapper.HDFMapper` constructs the mapping for
a given HDF5 file.  When a HDF5 file is opened with
:class:`~bapsflib.lapd.file.File`,
:class:`~bapsflib._hdf.maps.mapper.HDFMapper` is automatically called to
construct the map and an instance of the mapping object is bound
to the file object as :attr:`~bapsflib.lapd.file.File.file_map`.
Thus, the file mappings for :file:`test.hdf5` can be accessed like::

    >>> f = lapd.File('test.hdf5')
    >>> f.file_map
    <bapsflib._hdf.maps.mapper.HDFMapper>

.. include:: mapping.inc.rst
.. include:: add_map_module.inc.rst
