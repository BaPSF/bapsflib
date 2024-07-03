.. py:currentmodule:: bapsflib.lapd

The file mapping is key to :mod:`bapsflib`'s ability to provide a
consistent user interface to all the possible LaPD HDF5 file
configurations.  It acts as the translator between the package interface
and the HDF5 file structure.

The LaPD file mapping is constructed by the
:class:`~_hdf.lapdmap.LaPDMap` class, which sub-classes
:class:`~bapsflib._hdf.HDFMap` (see :ref:`hdfmap_details` for
:class:`~bapsflib._hdf.HDFMap` details), and an instance is bound to
the file object as :attr:`~File.file_map`.  Except for some select
cases, the :attr:`~File.file_map` object does not need to be directly
accessed.  Its results are provide through higher-level user interfaces,
such as the attributes/methods :attr:`~File.info`,
:attr:`~File.run_description`, :meth:`~File.read_data`, etc.  The
results can also be easily printed or saved using the
:attr:`~File.overview` attribute, see :ref:`file_overview` for details.

:numref:`LaPDMap_meth_table` shows the available attributes and methods
bound to :attr:`~File.file_map`.

.. _LaPDMap_meth_table:

.. csv-table:: Bound methods and attributes on :code:`f.file_map`.
    :header: "method/attribute", "Description"
    :widths: 20, 60

    :attr:`~_hdf.lapdmap.LaPDMap.controls`, "
    dictionary of control device mapping objects
    "
    :attr:`~_hdf.lapdmap.LaPDMap.digitizers`, "
    dictionary of digitizer mapping objects
    "
    :attr:`~_hdf.lapdmap.LaPDMap.exp_info`, "
    dictionary of experimental info collected from various *group*
    attributes in the HDF5 file
    "
    :meth:`~_hdf.lapdmap.LaPDMap.get`, "
    retrieve the mapping object for a specified device
    "
    :attr:`~_hdf.lapdmap.LaPDMap.is_lapd`, "
    :code:`True` if it was determined that the HDF5 file was generated
    by the LaPD
    "
    :attr:`~_hdf.lapdmap.LaPDMap.lapd_version`, "
    version string of the LaPD DAQ Controller software used to generate
    the HDF5 file
    "
    :attr:`~_hdf.lapdmap.LaPDMap.main_digitizer`, "
    mapping object for the digitizer that is considered the
    :ibf:`""main digitizer""`
    "
    :attr:`~_hdf.lapdmap.LaPDMap.msi`, "
    dictionary of MSI diagnostic mapping objects
    "
    :attr:`~_hdf.lapdmap.LaPDMap.run_info`, "
    dictionary of experimental run info collected from various *group*
    attributes in the HDF5 file
    "
    :attr:`~_hdf.lapdmap.LaPDMap.unknowns`, "
    list of all *subgroup* and *dataset* paths in the HDF5 root group,
    control device group, digitizer group, and MSI group that were
    unable to be mapped
    "
