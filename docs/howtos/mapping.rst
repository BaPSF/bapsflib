A file mapping is constructed by
:class:`~bapsflib.lapdhdf.hdfmapper.hdfMap` and its called daughter
routines.  When a HDF5 file is opened with
:class:`~bapsflib.lapdhdf.files.File`,
:class:`~bapsflib.lapdhdf.hdfmapper.hdfMap` is automatically called to
construct a file mapping and an instance of the mapping object is bound
to the file object as :attr:`~bapsflib.lapdhdf.files.File.file_map`.
Thus, the file mappings for :file:`test.hdf5` can be accessed like

    >>> f = lapdhdf.File('test.hdf5')
    >>> f.file_map
    Out: <bapsflib.lapdhdf.hdfmapper.hdfMap>

Basic Structure of :attr:`file_map` Mapping Object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _get_digitizers:

Retrieving Active Digitizers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A list of all detected digitizers can be obtain by doing

    >>> list(f.file_map.digitizers)

The file mappings for all the active digitizers are stored in the
dictionary :code:`f.file_map.digitizers` such that

    >>> list(f.file_map.digitizers.keys())
    Out: list of strings of all active digitizer names

    >>> f.file_map.digitizer[digi_name]
    Out: digitizer mapping object

Retrieving Active Digitizer Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _get_adcs:

Retrieving Active Analog-Digital Converts (adc's) for a Digitizer Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _get_conns:

Retrieving adc Connections and Digitization Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
