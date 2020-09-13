.. py:currentmodule:: bapsflib.lapd

Upon opening a file, :class:`~File` calls on the
:class:`~_hdf.lapdmap.LaPDMap` class
(a subclass of :class:`~bapsflib._hdf.maps.core.HDFMap`) to construct
a mapping of the HDF5 file's internal data structure.  This mapping
provides the necessary translation for the high-level data reading
methods, :meth:`~File.read_data`, :meth:`~File.read_controls`, and
:meth:`~File.read_msi`.  If an element of the HDF5 file
is un-mappable -- a mapping module does not exist or the mapping
fails -- the data can still be reached using the not-so-lower
inherited methods of :class:`h5py.File`.  An instance of the mapping
object is bound to :class:`File` as
:attr:`~File.file_map` ::

    >>> from bapsflib import lapd
    >>> from bapsflib._hdf import HDFMap
    >>> f = lapd.File('test.hdf5')
    >>> f.file_map
    <LaPDMap of HDF5 file 'test.hdf5'>
    >>>
    >>> # is still an instance of HDFMap
    >>> isinstance(f.file_map, HDFMap)
    True

For details on how the mapping works and how the mapping objects are
structured see :ref:`hdfmap_details`.  For details on using the
:attr:`~File.file_map` see :ref:`file_map` for details.

The opened file object (``f``) provides a set of high-level methods and
attributes for th user to interface with, see :numref:`f_meth_table`.

.. _f_meth_table:

.. csv-table:: Bound methods and attributes for open HDF5 file object
               :class:`File`
    :header: "method/attribute", "Description"
    :widths: 20, 60

    :attr:`~File.controls`, "
    dictionary of control device mappings (quick access to
    :attr:`f.file_map.controls`)
    "
    :attr:`~File.digitizers`, "
    dictionary of digitizer [device] mappings (quick access to
    :attr:`f.file_map.digitizers`)
    "
    :attr:`~File.file_map`, "
    | instance of the LaPD HDF5 file mapping (instance of
      :class:`~_hdf.lapdmap.LaPDMap`)
    | (see :ref:`file_map` for details)
    "
    :attr:`~File.info`, "
    | dictionary of meta-info about the HDF5 file and the experimental
      run
    | (see :ref:`file_info` for details)
    "
    :attr:`~File.msi`, "
    dictionary of MSI diagnostic [device] mappings (quick access to
    :attr:`f.file_map.msi`)
    "
    :attr:`~File.overview`, "
    | instance of :class:`~_hdf.lapdoverview.LaPDOverview`
      which that allows for printing and saving of the file mapping
      results
    | (see :ref:`file_overview` for details)
    "
    :meth:`~File.read_controls`, "
    | high-level method for reading control device data contained in the
      HDF5 file (instance of
      :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`)
    | (see :ref:`read_controls` for details)
    "
    :meth:`~File.read_data`, "
    | high-level method for reading digitizer data and mating control
      device data at the time of read (instance of
      :class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`)
    | (see :ref:`read_digi` for details)
    "
    :meth:`~File.read_msi`, "
    | high-level method for reading MSI diagnostic date (instance of
      :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`)
    | (see :ref:`read_msi` for details)
    "
    :meth:`~File.run_description`, "
    printout the LaPD experimental run description
    (:code:`print(f.info['run description'].splitlines())`)
    "
