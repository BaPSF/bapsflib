Extracting data from an HDF5 file is done with either the
:meth:`~bapsflib.lapdhdf.files.File.read_data` method or the
:meth:`~bapsflib.lapdhdf.files.File.read_controls` method.  The
:meth:`~bapsflib.lapdhdf.files.File.read_controls` method is designed to
extract data from probe control devices (e.g. the *6K Compumotor*, the
*waveform generator*, etc.), where as, the
:meth:`~bapsflib.lapdhdf.files.File.read_data` method is designed to
extract digitizer data and mate that data with control data.  Details on
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
    silent, :code:`False`, "set :code:`True` to suppress command line
    printout of soft-warnings
    "

that are explained in more detail in the following sections.  Assuming
the :file:`test.hdf5` file has only one digitizer, one adc, and one
configuration, then all the data recorded on :code:`board = 1` and
:code:`channel = 0` can be extracted as follows

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
