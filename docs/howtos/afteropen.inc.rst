Upon opening a file, :class:`~bapsflib.lapdhdf.files.File` calls on the
:class:`~bapsflib.lapdhdf.hdfmapper.hdfMap` class to construct a
mapping of the HDF5 file's internal data structure, see section
:ref:`file_mappings` for details on the mapping construction.  Since the
various elements in the HDF5 data structure defined by the LaPD DAQ
system can evolve over time, the purpose of the mapping construction is
to provide a translation of the evolving data structure into a universal
format that will be consistent over time for both the user and the
:mod:`bapsflib` methods. An instance of the mapping object is bound to
:class:`~bapsflib.lapdhdf.files.File` as
:attr:`~bapsflib.lapdhdf.files.File.file_map`

.. code-block:: python3

    >>> f = lapdhdf.File('test.hdf5')
    >>> f.file_map
    <bapsflib.lapdhdf.hdfmapper.hdfMap>

This mapping object is used by :mod:`bapsflib`'s high-level functions
to collect data requested by the user.  The user can also delve into the
mapping object to learn about the setup and configurations for the
various devices (digitizers, control devices, MSI diagnostics, etc.)
used in the experimental run. [*]_

The opened file object (``f``) provides a set of high-level methods and
attributes for th user to interface with, see :numref:`f_meth_table`.

.. _f_meth_table:

.. csv-table:: Bound methods and attributes for open HDF5 file object
               :class:`~bapsflib.lapdhdf.files.File`
    :header: "method/attribute", "Description"
    :widths: 20, 60

    :attr:`~bapsflib.lapdhdf.files.File.file_map`, "instance of the
    HDF5 file mapping (:class:`~bapsflib.lapdhdf.hdfmapper.hdfMap`)
    "
    :attr:`~bapsflib.lapdhdf.files.File.info`, "dictionary of general
    info on the HDF5 file and experimental run (see section
    :ref:`file_info`)
    "
    :attr:`~bapsflib.lapdhdf.files.File.list_controls`, "list naming all
    successfully mapped control devices
    "
    :attr:`~bapsflib.lapdhdf.files.File.list_digitizers`, "list naming
    all successfully mapped digitizers
    "
    :attr:`~bapsflib.lapdhdf.files.File.list_file_items`, "list of paths
    for all items (Groups and Datasets) in the HDF5 data structure
    "
    :attr:`~bapsflib.lapdhdf.files.File.list_msi`, "list naming  all
    successfully mapped MSI diagnostics
    "
    :attr:`~bapsflib.lapdhdf.files.File.overview`, "instance of
    :class:`~bapsflib.lapdhdf.hdfoverview.hdfOverview` that allows for
    printing and saving of the file mapping results, see
    :ref:`file_hdfoverview` for details
    "
    :meth:`~bapsflib.lapdhdf.files.File.read_controls`, "function to
    read control device data (see section on reading
    :ref:`read_controls`)
    "
    :meth:`~bapsflib.lapdhdf.files.File.read_digitizer`, "function to
    read digitizer data and mate control device data (see section on
    reading :ref:`read_digi`)
    "
    :meth:`~bapsflib.lapdhdf.files.File.read_msi`, "function to
    read MSI diagnostic (see section on reading :ref:`read_msi`)
    "
    :meth:`~bapsflib.lapdhdf.files.File.run_description`, "printout of
    experimental run descriptions
    (:code:`print(f.info['run description'].splitlines())`)
    "

.. [*] add a link to section on using the
    :attr:`~bapsflib.lapdhdf.files.File.file_map` attribute once written
