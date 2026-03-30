Opening a HDF5 file is done using the `bapsflib.lapd.File` class.
`~bapsflib.lapd.File` subclasses `h5py.File`, so *group* and  *dataset*
manipulation is handled by the inherited methods; whereas,  the new
methods (see :numref:`f_meth_table`) are focused on mapping the  data
structure and providing a high-level access to the experimental data
recorded by the LaPD DAQ system.

`~bapsflib.lapd.File` is a wrapper on `h5py.File` and, thus, HDF5 file
manipulation is handled by the inherited methods of `h5py.File`.
`~bapsflib.lapd.File` adds methods and attributes specifically for
manipulating data and metadata written to the file from the Large
Plasma Device (LaPD) DAQ system, see :numref:`f_meth_table`.

To open a LaPD generated HDF5 file do

.. code-block:: python3

    >>> import h5py
    >>> from bapsflib import lapd
    >>> f = lapd.File('test.hdf5')
    >>> f
    <HDF5 file "test.hdf5" (mode r)>
    >>>
    >>> # f is still an instance of h5py.File
    >>> isinstance(f, h5py.File)
    True

which opens the file as 'read-only' by default. `~bapsflib.lapd.File`
restricts opening modes to 'read-only' (``mode='r'``) and 'read/write'
(``mode='r+'``), but maintains keyword pass-through to
`h5py.File`.
