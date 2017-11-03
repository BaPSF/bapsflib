Extracting data from an HDF5 file is done with either the
:meth:`~bapsflib.lapdhdf.files.File.read_data` method or the
:meth:`~bapsflib.lapdhdf.files.File.read_controls` method.  The
:meth:`~bapsflib.lapdhdf.files.File.read_controls` method is designed to
extract data from probe control devices (e.g. the *6K Compumotor*, the
*waveform generator*, etc.), where as, the
:meth:`~bapsflib.lapdhdf.files.File.read_data` method is designed to
extract digitizer data and mate any specified control data.  Details on
using the :meth:`~bapsflib.lapdhdf.files.File.read_controls` method can
be read in the :ref:`read_controls` section.  This section will focus on
the functionality of :meth:`~bapsflib.lapdhdf.files.File.read_data`.

At a minimum the :meth:`~bapsflib.lapdhdf.files.File.read_data` method
only needs a board number and channel number to extract data, but there
are several additional keyword options:

.. csv-table::
    :header: "Keyword", "Default", "Description"
    :widths: 15, 10, 40

    :ref:`index <read_w_index>`, :code:`None`, "row index of the HDF5
    dataset
    "
    "shotnum", ":code:`None`", "global HDF5 file shot number
    "
    :ref:`digitizer <read_w_digitizer>`, :code:`None`, "name of
    digitizer for which :code:`board` and :code:`channel` belong to
    "
    :ref:`adc <read_w_adc>`, :code:`None` , "name of the digitizer
    analog-digitial-converter for which :code:`board` and
    :code:`channel` belong to
    "
    :ref:`config_name <read_w_config_name>`, :code:`None`, "name of the
    digitizer configuration
    "
    :ref:`keep_bits <read_w_keep_bits>`, :code:`False`, "set
    :code:`True` to keep the extracted digitizer data in bits opposed to
    voltage
    "
    add_controls, :code:`None`, "list of control devices whose data will
    be matched and added to the requested digitizer data
    "
    intersection_set, :code:`True`, "ensures that the returned data
    array only contains :code:`shotnum`'s that are inclusive in the
    digitizer dataset adn all control device datasets
    "
    :data:`silent`, :code:`False`, "set :code:`True` to suppress command
    line printout of soft-warnings
    "

that are explained in more detail in the following sections.

If the :file:`test.hdf5` file has only one digitizer with one active
adc and one configuration, then the entire dataset collected from the
signal attached to :code:`board = 1` and :code:`channel = 0` can be
extracted as follows:

    >>> from bapsflib import lapdhdf
    >>> f = lapdhdf.File('test.hdf5')
    >>> board, channel = 1, 0
    >>> data = f.read_data(baord, channel)

where :obj:`data` is an instance of
:class:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData`.  The
:class:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData` class acts as a
wrapper on :class:`numpy.recarray`.  Thus, :obj:`data` behaves just like
a :class:`numpy.recarray` object, but will have additional methods and
attributes that describe the data's origin and parameters (e.g.
:attr:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData.info`,
:attr:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData.dt`,
:attr:`~bapsflib.lapdhdf.hdfreaddata.hdfReadData.dv`, etc.).

By default, :obj:`data` is a structured :mod:`numpy` array with the
following :data:`dtype`:

    >>> data.dtype
    Out[0]:
    dtype([('shotnum', '<u4'),
           ('signal', '<f4', (12288,)),
           ('xyz', '<f4', (3,))])

where :code:`'shotnum'` contains the HDF5 shot number, :code:`'signal'`
contains the signal recorded by the digitizer, and :code:`'xyz'` is a
3-element array containing the probe position.  In this example,
the digitized signal is automatically converted into voltage before
being added to the array and :code:`12288` is the size of the signal's
time-array.  To keep the digitizer :code:`'signal` in bit values, then
set :code:`keep_bits=True` at execution of
:meth:`~bapsflib.lapdhdf.files.File.read_data`.  The field :code:`'xyz'`
is initialized with :const:`numpy.nan` values, but will be filled out if
an appropriate control device is specified (see :ref:`adding_controls`).

For details on handling and manipulating :data:`data` see
:ref:`handle_data`.

.. note::

    Since :class:`bapsflib.lapdhdf` leverages the :class:`h5py` package,
    the data in :file:`test.hdf5` resides on disk until one of the read
    methods, :meth:`~bapsflib.lapdhdf.files.File.read_data` or
    :meth:`~bapsflib.lapdhdf.files.File.read_data`, is called.  In
    calling on of these methods, the requested data is brought into
    memory as a :class:`numpy.ndarray` and a :class:`numpy.view` onto
    that :data:`ndarray` is returned to the user.

.. _read_subset:

Extracting a Sub-set
^^^^^^^^^^^^^^^^^^^^

Sub-setting behavior is determined by keywords :data:`index`,
:data:`shotnum`, and :data:`intersection_set`.

.. _read_w_index:

Using :data:`index` keyword
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

To see how to retrieve a list of active adc's, then look to
:ref:`get_digitizers`.

.. _read_w_adc:

Using :data:`adc` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^

A digitizer may have several analog-digital converts (adc's).  For
example, the :code:`'SIS crate'` digitizer can digitized data with two
different adc's, :code:`'SIS 3302'` and :code:`'SIS 3305'`.  By default,
if only one adc's is active then
:meth:`~bapsflib.lapdhdf.files.File.read_data` method will assume that
one.  If two or more adc's are active then
:meth:`~bapsflib.lapdhdf.files.File.read_data` will the adc with the
slower sample rate.  In the case above, that would be
:code:`'SIS 3302'`.  To extract data from :code:`'SIS 3305'`, then one
would do

    >>> data = f.read_data(0, 0, adc='SIS 3305')

To see how to retrieve a list of active adc's, then look to
:ref:`get_adcs`.

.. _read_w_config_name:

Using :data:`config_name` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. _read_w_keep_bits:

Using :data:`keep_bits` keyword
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. _adding_controls:

Adding Control Device Data
^^^^^^^^^^^^^^^^^^^^^^^^^^
