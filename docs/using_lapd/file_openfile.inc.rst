Opening a HDF5 file is done using the
:class:`bapsflib.lapd.File` class.
:class:`~bapsflib.lapd.File` is a wrapper on
:class:`h5py.File` and, thus, HDF5 file manipulation is handled by the
inherited methods of :class:`h5py.File`.
:class:`~bapsflib.lapd.File` adds methods and
attributes specifically for manipulating data and metadata written to
the file from the Large Plasma Device (LaPD) DAQ system, see
:numref:`f_meth_table`.

To open a LaPD generated HDF5 file do

.. code-block:: python3

    >>> from bapsflib import lapd
    >>> f = lapd.File('test.hdf5')
    >>> f
    <HDF5 file "test.hdf5" (mode r)>

which opens the file as 'read-only' by default and is equivalent to

    >>> from bapsflib import lapd
    >>> f = lapd.File('test.hdf5')
    >>> f
    <HDF5 file "test.hdf5" (mode r)>

which opens the file as 'read-only' by default and is equivalent to

    >>> from bapsflib import lapd
    >>> f = lapd.File('test.hdf5')
    >>> f
    <HDF5 file "test.hdf5" (mode r)>

which opens the file as 'read-only' by default and is equivalent to

.. code-block:: python3

    >>> import h5py
    >>> f = h5py.File('test.hdf5', 'r')
    >>> f
    <HDF5 file "test.hdf5" (mode r)>
