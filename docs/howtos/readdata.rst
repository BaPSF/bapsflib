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
brought into memory as a :class:`numpy.ndarray` and
:meth:`~bapsflib.lapdhdf.files.File.read_data` returns a :meth:`view`
onto that array.

.. _read_w_shots:

Using :data:`shots` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _read_w_digitizer:

Using :data:`digitizer` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _read_w_adc:

Using :data:`adc` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^

.. _read_w_config_name:

Using :data:`config_name` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _read_w_keep_bits:

Using :data:`keep_bits` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
