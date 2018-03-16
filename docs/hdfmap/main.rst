.. _file_mappings:

HDF5 File Mapping (:class:`~bapsflib.lapdhdf.hdfmapper.hdfMap`)
===============================================================

.. contents:: Contents
    :depth: 3
    :local:

:class:`~bapsflib.lapdhdf.hdfmapper.hdfMap` constructs the mapping for
a given HDF5 file.  When a HDF5 file is opened with
:class:`~bapsflib.lapdhdf.files.File`,
:class:`~bapsflib.lapdhdf.hdfmapper.hdfMap` is automatically called to
construct the map and an instance of the mapping object is bound
to the file object as :attr:`~bapsflib.lapdhdf.files.File.file_map`.
Thus, the file mappings for :file:`test.hdf5` can be accessed like::

    >>> f = lapdhdf.File('test.hdf5')
    >>> f.file_map
    <bapsflib.lapdhdf.hdfmapper.hdfMap>

.. include:: mapping.inc.rst
.. include:: add_map_module.inc.rst