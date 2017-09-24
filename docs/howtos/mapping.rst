The constructed file mapping object for a LaPD generated HDF5 file is
bound to the file object as the property :attr:`file_map`

    >>> f = lapdhdf.File('test.hdf5')
    >>> f.file_map
    Out: <bapsflib.lapdhdf.hdfmappers.hdfMap>

Basic Structure of :attr:`file_map` Mapping Object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Retrieving Active Digitizers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The file mappings for all the active digitizers are stored in the
dictionary :code:`f.file_map.digitizers` such that

    >>> list(f.file_map.digitizers.keys())
    Out: list of strings of all active digitizer names

    >>> f.file_map.digitizer[digi_name]
    Out: digitizer mapping object

Retrieving Active Digitizer Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Retrieving Active Analog-Digital Converts (adc's) for a Digitizer Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Retrieving adc Connections and Digitization Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
