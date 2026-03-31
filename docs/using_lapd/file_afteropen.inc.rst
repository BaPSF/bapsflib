.. py:currentmodule:: bapsflib.lapd

Upon opening a file, `~bapsflib.lapd._hdf.file.File` calls on the
`~_hdf.mapper.LaPDMapper` class (a subclass of
`~bapsflib._hdf.maps.mapper.HDFMapper`) to construct a mapping of the
HDF5 file's internal data structure.  This mapping provides the
necessary translation for the high-level data reading methods,
:meth:`~bapsflib.lapd._hdf.file.File.read_data`,
:meth:`~bapsflib.lapd._hdf.file.File.read_controls`, and
:meth:`~bapsflib.lapd._hdf.file.File.read_msi`.  If an element of the
HDF5 file is un-mappable -- a mapping module does not exist or the
mapping fails -- the data can still be reached using the not-so-lower
inherited methods of `h5py.File`.  An instance of the mapping
object is bound to `~bapsflib.lapd._hdf.file.File` as
:attr:`~bapsflib.lapd._hdf.file.File.file_map` ::

    >>> from bapsflib import lapd
    >>> from bapsflib._hdf import HDFMapper
    >>> f = lapd.File('test.hdf5')
    >>> f.file_map
    <LaPDMapper of HDF5 file 'test.hdf5'>
    >>>
    >>> # is still an instance of HDFMapper
    >>> isinstance(f.file_map, HDFMapper)
    True

For details on how the mapping works and how the mapping objects are
structured see :ref:`hdfmap_details`.  For details on using the
:attr:`~bapsflib.lapd._hdf.file.File.file_map` see :ref:`file_map` for
details.

The opened file object (``f``) provides a set of high-level methods and
attributes for th user to interface with, see :numref:`f_meth_table`.

.. _f_meth_table:

.. csv-table:: Bound methods and attributes for open HDF5 file object
               `File`
    :header: "method/attribute", "Description"
    :widths: 20, 60

    :attr:`~bapsflib.lapd._hdf.file.File.controls`, "
    dictionary of control device mappings (quick access to
    :attr:`f.file_map.controls`)
    "
    :attr:`~bapsflib.lapd._hdf.file.File.digitizers`, "
    dictionary of digitizer [device] mappings (quick access to
    :attr:`f.file_map.digitizers`)
    "
    :attr:`~bapsflib.lapd._hdf.file.File.file_map`, "
    | instance of the LaPD HDF5 file mapping (instance of
      `~_hdf.mapper.LaPDMapper`)
    | (see :ref:`file_map` for details)
    "
    :attr:`~bapsflib.lapd._hdf.file.File.info`, "
    | dictionary of meta-info about the HDF5 file and the experimental
      run
    | (see :ref:`file_info` for details)
    "
    :attr:`~bapsflib.lapd._hdf.file.File.msi`, "
    dictionary of MSI diagnostic [device] mappings (quick access to
    :attr:`f.file_map.msi`)
    "
    :attr:`~bapsflib.lapd._hdf.file.File.overview`, "
    | instance of `~_hdf.lapdoverview.LaPDOverview`
      which that allows for printing and saving of the file mapping
      results
    | (see :ref:`file_overview` for details)
    "
    :meth:`~bapsflib.lapd._hdf.file.File.read_controls`, "
    | high-level method for reading control device data contained in the
      HDF5 file (instance of
      `~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`)
    | (see :ref:`read_controls` for details)
    "
    :meth:`~bapsflib.lapd._hdf.file.File.read_data`, "
    | high-level method for reading digitizer data and mating control
      device data at the time of read (instance of
      `~bapsflib._hdf.utils.hdfreaddata.HDFReadData`)
    | (see :ref:`read_digi` for details)
    "
    :meth:`~bapsflib.lapd._hdf.file.File.read_msi`, "
    | high-level method for reading MSI diagnostic date (instance of
      `~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`)
    | (see :ref:`read_msi` for details)
    "
    :meth:`~bapsflib.lapd._hdf.file.File.run_description`, "
    printout the LaPD experimental run description
    (``print(f.info['run description'].splitlines())``)
    "
