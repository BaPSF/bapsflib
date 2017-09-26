Reading data from an HDF5 file is straight forward using the
:meth:`~bapsflib.lapdhdf.files.File.read_data` method on the
:class:`~bapsflib.lapdhdf.files.File` class.  At a minimum, the
:meth:`~bapsflib.lapdhdf.files.File.read_data` method only needs a board
number and channel number, but there are several additional keyword
options:

* :ref:`shots <read_w_shots>`
* :ref:`digitizer <read_w_digitizer>`
* :ref:`adc <read_w_adc>`
* :ref:`config_name <read_w_config_name>`
* :ref:`keep_bits <read_w_keep_bits>`

that are explained in more detail below.  Assuming the :file:`test.hdf5`
file has only one digitizer, one adc, and one configuration, then all
the data recorded on :code:`board = 1` and :code:`channel = 0` can be
extracted as follows

    >>> from bapsflib import lapdhdf
    >>> f = lapdhdf.File('test.hdf5')
    >>> board, channel = 1, 0
    >>> data = f.read_data(baord, channel)
    >>> data
    Out: hdfReadData([[..., ], [..., ], ..., [..., ]])

where :code:`data` is an instance of
:class:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData`.  The
:class:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData` class acts as a
wrapper on :class:`numpy.ndarray`, so :code:`data` behaves just like a
:class:`ndarray` with additional attached methods and attributes (e.g.
:attr:`info`, :attr:`dt`, :attr:`dv`, etc.).

Before calling :meth:`~bapsflib.lapdhdf.files.File.read_data` the data
in :file:`test.hdf5` resides on disk.  By calling
:meth:`~bapsflib.lapdhdf.files.File.read_data` the requested data is
brought into memory as a :class:`numpy.ndarray`, converted from bits to
voltage, and returned as a :meth:`view` onto that array.

.. _read_w_shots:

Using :data:`shots` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :code:`shots` keyword allows for a subset of the data to be
extracted from the HDF5 file.  This is useful when only a fraction of
the data needs to be manipulated, since
:meth:`~bapsflib.lapdhdf.files.File.read_data` will only bring that
subset of data into memory.  If :code:`shots` is not specified, then all
shots are extracted.

The :code:`shots` keyword can be an :code:`int`, list of :code:`ints`,
or a :func:`slice` object.  Suppose the HDF5 dataset (:code:`dset`) has
a shape of

    >>> dset.shape
    Out: (100, 3000)

The first dimension corresponds to the the :code:`shots` index and the
second dimension corresponds to the time index.  To read out just shot 4
then

    >>> data = f.read_data(0, 0, shots=4)

which is equivalent to

    >>> data = dset[4].view()

To read out shots 4, 7, and 10 then

    >>> data = f.read_data(0, 0, shots=[4, 7, 10])

which is equivalent to

    >>> data = dset[(4, 7, 10), :].view()

To read out a slice of shots from 4 to 10 then

    >>> data = f.read_data(0, 0, shots=slice(4, 11, None))

which is equivalent to

    >>> data = dset[4:11:, :].view()

To read out every other shot between 4 and 10 then

    >>> data = f.read_data(0, 0, shots=slice(4, 11, 2))

which is equivalent to

    >>> data = dset[4:11:2, :].view()


.. _read_w_digitizer:

Using :data:`digitizer` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A HDF5 may contain data from more than one digitizer.  In such a
situation, the :data:`digitizer` keyword can be used to direct the
:meth:`~bapsflib.lapdhdf.files.File.read_data` method to extract data
from the desired digitizer.  If the keyword is omitted, then
:meth:`~bapsflib.lapdhdf.files.File.read_data` will assume the digitizer
defined in :attr:`~bapsflib.lapdhdf.files.File.file_map`'s
:attr:`~bapsflib.lapdhdf.hdfmappers.hdfMap.main_digitizer` property.

Suppose the :file:`test.hdf5` file has two digitizers,
:code:`'SIS 3301'` and :code:`'SIS crate'`.  In this case,
:code:`'SIS 3301'` would be assumed as the
:attr:`~bapsflib.lapdhdf.hdfmappers.hdfMap.main_digitizer`.  In order to
extract data from :code:`'SIS crate'` one would do

    >>> data = f.read_data(0, 0, digitizer='SIS crate')

A list of all detected digitizers can be obtain by doing

    >>> list(f.file_map.digitizers)

.. _read_w_adc:

Using :data:`adc` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^

.. _read_w_config_name:

Using :data:`config_name` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _read_w_keep_bits:

Using :data:`keep_bits` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
