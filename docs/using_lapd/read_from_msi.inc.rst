MSI diagnostic data is read using the
:meth:`~bapsflib.lapd.File.read_msi` method on `~bapsflib.lapd.File`.
Only the MSI diagnostic name needs to be supplied to read the
associated data::

    >>> from bapsflib import lapd
    >>>
    >>> # open file
    >>> f = lapd.File('test.hdf5')
    >>>
    >>> # list mapped MSI diagnostics
    >>> f.list_msi
    ['Discharge',
     'Gas pressure',
     'Heater',
     'Interferometer array',
     'Magnetic field']
    >>>
    >>> # read 'Discharge' data
    >>> mdata = f.read_msi('Discharge')

The returned data ``mdata`` is a structured `numpy` array where
its field structure and population is determined by the MSI diagnostic
mapping object. Every ``mdata`` will have the fields ``'shotnum'``
and ``'meta'``. ``'shotnum'`` represents the HDF5 shot number.
``'meta'`` is a structured array with fields representing quantities
(metadata) that are both diagnostic and shot number specific, but are
not considered "primary" data arrays.  Any other field in ``mdata`` is
considered to be a "primary" data array. Continuing with the above
example::

    >>> # display mdata dytpe
    >>> mdata.dtype
    dtype([('shotnum', '<i4'),
           ('voltage', '<f4', (2048,)),
           ('current', '<f4', (2048,)),
           ('meta', [('timestamp', '<f8'),
                     ('data valid', 'i1'),
                     ('pulse length', '<f4'),
                     ('peak current', '<f4'),
                     ('bank voltage', '<f4')])])
    >>>
    >>> # display shot numbers
    >>> mdata['shotnum']
    array([    0, 19251], dtype=int32)

Here, the fields ``'voltage'`` and ``'current'`` correspond to
"primary" data arrays.  To display display the first three samples of
the ``'voltage'`` array for shot number **19251** do::

    >>> mdata['voltage'][1][0:3:]
    array([-44.631958, -44.708252, -44.631958], dtype=float32)

The metadata field ``'meta'`` has five quantities in it,
``'timestamp'``, ``'data valid'``, ``'pulse length'``,
``'peak current'``, and ``'peak voltage'``.  Now, these metadata
fields will vary depending on the requested MSI diagnostic.  To view
the ``'peak voltage'`` for shot number **0** do::

    >>> mdata['meta']['peak voltage'][0]
    6127.1323

The data array ``mdata`` is also constructed with a :attr:`info`
attribute that contains metadata that is diagnostic specific but not
shot number specific.

.. code-block:: python

    >>> mdata.info
    {'current conversion factor': [0.0],
     'diagnostic name': 'Discharge',
     'diagnostic path': '/MSI/Discharge',
     'dt': [4.88e-05],
     'hdf file': 'test.hdf5',
     't0': [-0.0249856],
     'voltage conversion factor': [0.0]}

Every :attr:`info` attribute will have the keys ``'hdf file'``,
``'diagnostic name'``, and ``'diagnostic path'``.  The rest of
the keys will be MSI diagnostic dependent.  For example,
``mdata.info`` for the ``'Magnetic field'`` diagnostic would have the
key ``'z'`` that corresponds to the axial locations of the magnetic
field array.

.. code-block:: python

    >>> # get magnetic field data
    >>> mdata = f.read_msi('Magnetic field')
    >>> mdata.dtype
    dtype([('shotnum', '<i4'),
           ('magnet ps current', '<f4', (10,)),
           ('magnetic field', '<f4', (1024,)),
           ('meta', [('timestamp', '<f8'),
                     ('data valid', 'i1'),
                     ('peak magnetic field', '<f4')])])
    >>> mdata.info
    {'diagnostic name': 'Magnetic field',
     'diagnostic path': '/MSI/Magnetic field',
     'hdf file': 'test.hdf5',
     'z': array([-300.     , -297.727  , -295.45395, ..., 2020.754  ,
                 2023.027  , 2025.3    ], dtype=float32)}
