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

    :data:`index`, :code:`None`, "row index of the HDF5 dataset
    "
    ":data:`shotnum`", ":code:`None`", "global HDF5 file shot number
    "
    :data:`digitizer`, :code:`None`, "name of digitizer for which
    :code:`board` and :code:`channel` belong to
    "
    :data:`adc`, :code:`None` , "name of the digitizer
    analog-digital-converter for which :code:`board` and :code:`channel`
    belong to
    "
    :data:`config_name`, :code:`None`, "name of the digitizer
    configuration
    "
    :data:`keep_bits`, :code:`False`, "set :code:`True` to keep the
    extracted digitizer data in bits opposed to voltage
    "
    :data:`add_controls`, :code:`None`, "list of control devices whose
    data will be matched and added to the requested digitizer data
    "
    :data:`intersection_set`, :code:`True`, "ensures that the returned
    data array only contains :code:`shotnum`'s that are inclusive in the
    digitizer dataset adn all control device datasets
    "
    :data:`silent`, :code:`False`, "set :code:`True` to suppress command
    line printout of soft-warnings
    "

that are explained in more detail in the following subsections.

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

Extracting a sub-set
^^^^^^^^^^^^^^^^^^^^

.. Sub-setting behavior is determined by three keywords: :data:`index`,
   :data:`shotnum`, and :data:`intersection_set`.

There are three keywords for sub-setting a dataset: :data:`index`,
:data:`shotnum`, and :data:`intersection_set`.  :data:`index` and
:data:`shotnum` are indexing keywords, whereas, :data:`intersection_set`
controls sub-setting behavior between the indexing keywords and the
dataset(s).

:data:`index` refers to the row index of the requested dataset and
:data:`shotnum` refers to the global HDF5 shot number.  Either indexing
keyword can be used, but :data:`shotnum` will always override
:data:`index`.  :data:`index` and :data:`shotnum` can be of :func:`type`
:code:`int`, :code:`list(int)`, or :func:`slice`.  Sub-setting with
:data:`index` looks like:

    >>> # read dataset row 10
    >>> data = f.read_data(board, channel, index=10)
    >>> # read dataset rows 10, 20, and 30
    >>> data = f.read_data(board, channel, index=[10, 20, 30])
    >>> # read dataset rows 10 to 19
    >>> data = f.read_data(board, channel, index=slice(10, 20))
    >>> # read every other dataset row from 10 to 19
    >>> data = f.read_data(board, channel, index=slice(10, 20, 2))

and with :data:`shotnum` looks like:


    >>> # read dataset shot number 10
    >>> data = f.read_data(board, channel, shotnum=10)
    >>> # read dataset shot numbers 10, 20, and 30
    >>> data = f.read_data(board, channel, shotnum=[10, 20, 30])
    >>> # read dataset shot numbers 10 to 19
    >>> data = f.read_data(board, channel, shotnum=slice(10, 20))
    >>> # read every 5th dataset shot number from 10 to 19
    >>> data = f.read_data(board, channel, index=slice(10, 20, 5))

:data:`intersection_set` modifies what shot numbers are returned by
:meth:`~bapsflib.lapdhdf.files.File.read_data`.  If :data:`index` is
used and no control device datasets are being mated to the digitizer
dataset, then :data:`intersection_set` has no affect on the returned
data array.  If :data:`shotnum` is used, then
:code:`intersection_set=True` (DEFAULT) will ensure that the returned
data array only contains shot numbers that are specified by
:code:`shotnum` and are in the digitizer dataset.  If set to
:code:`False`, then the returned array will contain all shot numbers
specified by :code:`shotnum` and any shot numbers not found in the
digitizer dataset will be filled with :code:`numpy.nan` values.

.. _read_digi:

Directing to a Specified Digitizer Dataset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible for a LaPD generated HDF5 file to contain multiple
digitizers, which can have multiple analog-digital-converters and
multiple data configurations.  In this case,
:meth:`~bapsflib.lapdhdf.files.File.read_data` utilizes keywords
:data:`digitizer`, :data:`adc`, and :data:`config_name` to redirect the
data extraction accordingly.

If :data:`digitizer` is not specified, then it is assumed that the
desired digitizer is the one defined in
:attr:`~bapsflib.lapdhdf.hdfmappers.hdfMap.main_digitizer`.  Suppose
the :file:`test.hdf5` has two digitizers, :code:`'SIS 3301'` and
:code:`'SIS crate'`.  In this case :code:`'SIS 3301'` would be assumed
as the :attr:`~bapsflib.lapdhdf.hdfmappers.hdfMap.main_digitizer`.  To
extract data from :code:`'SIS crate'` one would use the
:data:`digitizer` keyword as follows

    >>> data = f.read_data(board, channel, digitizer='SIS crate')

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
