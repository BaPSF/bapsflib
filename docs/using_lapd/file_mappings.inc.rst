.. py:currentmodule:: bapsflib.lapd

The main purpose of the :attr:`~File.file_map` object is to (1) identify
the control devices, digitizers, and MSI diagnostic in the HDF5 file and
(2) provide the necessary translation info to allow for easy reading of
data via :meth:`~File.read_controls`, :meth:`~File.read_data`, and
:meth:`~File.read_msi`.  For the most part, there is not reason to
directly access the :attr:`~File.file_map` object since its results can
easily be printed or saved using the :attr:`~File.overview` attribute,
see :ref:`file_overview` for details.  However, the mapping objects do
contain useful details that are desirable in certain circumstances and
can be modified for a special type of control device to augment the
resulting numpy array when data is read.

The file map object :attr:`~File.file_map` is an instance of
:class:`~_hdf.lapdmap.LaPDMap`, which subclasses
:class:`~bapsflib._hdf.HDFMap` (details on
:class:`~bapsflib._hdf.HDFMap` can be found at :ref:`hdfmap_details`).
The :class:`~_hdf.lapdmap.LaPDMap` provides a useful set of bound
methods, see :numref:`LaPDMap_meth_table`.

.. _LaPDMap_meth_table:

.. csv-table:: Bound methods and attributes on :data:`f.file_map`.
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
