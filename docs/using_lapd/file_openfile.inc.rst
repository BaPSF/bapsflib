Opening a HDF5 file is done using the
:class:`bapsflib.lapd.File` class.  :class:`~bapsflib.lapd.File`
subclasses :class:`h5py.File`, so *group* and *dataset* manipulation
is handled by the inherited methods; whereas, the new methods (see
:numref:`f_meth_table`) are focused on mapping the data structure and
providing a high-level access to the experimental data recorded by the
LaPD DAQ system.

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
    >>>
    >>> # f is still an instance of h5py.File
    >>> isinstance(f, h5py.File)
    True

which opens the file as 'read-only' by default.
:class:`~bapsflib.lapd.File` restricts opening modes to 'read-only'
(:code:`mode='r'`) and 'read/write' (:code:`mode='r+'`), but maintains
keyword pass-through to :class:`h5py.File`.