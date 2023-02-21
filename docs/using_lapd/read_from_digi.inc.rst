Digitizer data is read using the
:meth:`~bapsflib.lapd.File.read_data` method on
:class:`~bapsflib.lapd.File`.  The method also has the option
of mating control device data at the time of declaration (see section
:ref:`read_digi_adding_controls`) [#]_.

At a minimum the :meth:`~bapsflib.lapd.File.read_data` method
only needs a board number and channel number to extract data [#]_, but
there are several additional keyword options:

.. csv-table:: Optional keywords for
               :meth:`~bapsflib.lapd.File.read_data`
    :header: "Keyword", "Default", "Description"
    :widths: 10, 5, 40

    :data:`index`, :code:`slice(None)`, "row index of the HDF5 dataset
    (see :ref:`read_digi_subset`)
    "
    ":data:`shotnum`", ":code:`slice(None)`", "global HDF5 file shot
    number (see :ref:`read_digi_subset`)
    "
    :data:`digitizer`, :code:`None`, "
    | name of the digitizer for which :code:`board` and :code:`channel`
      belong to
    | (see :ref:`read_digi_digi`)
    "
    :data:`adc`, :code:`None` , "
    | name of the digitizer's analog-digital-converter (adc) for which
      :code:`board` and :code:`channel` belong to
    | (see :ref:`read_digi_digi`)
    "
    :data:`config_name`, :code:`None`, "
    | name of the digitizer configuration
    | (see :ref:`read_digi_digi`)
    "
    :data:`keep_bits`, :code:`False`, "Set :code:`True` to return the
    digitizer data in bit values. By default the digitizer data is
    converted to voltage.
    "
    :data:`add_controls`, :code:`None`, "
    | list of control devices whose data will be matched and added to
      the requested digitizer data
    | (see :ref:`read_digi_adding_controls`
    "
    :data:`intersection_set`, :code:`True`, "
    | Ensures that the returned data array only contains shot numbers
      that are inclusive in :code:`shotnum`, the digitizer dataset, and
      all control device datasets.
    | (see :ref:`read_digi_subset`)
    "
    :data:`silent`, :code:`False`, "set :code:`True` to suppress command
    line printout of soft-warnings
    "

These keywords are explained in more detail in the following
subsections.

If the :file:`test.hdf5` file has only one digitizer with one active
adc and one configuration, then the entire dataset collected from the
signal attached to :code:`board = 1` and :code:`channel = 0` can be
extracted as follows::

    >>> from bapsflib import lapd
    >>> f = lapd.File('test.hdf5')
    >>> board, channel = 1, 0
    >>> data = f.read_data(board, channel)

where :obj:`data` is an instance of
:class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`.  The
:class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData` class acts as a
wrapper on :class:`numpy.recarray`.  Thus, :obj:`data` behaves just like
a :class:`numpy.recarray` object, but will have additional methods and
attributes that describe the data's origin and parameters (e.g.
:attr:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData.info`,
:attr:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData.dt`,
:attr:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData.dv`, etc.).

By default, :obj:`data` is a structured :mod:`numpy` array with the
following :data:`dtype`::

    >>> data.dtype
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
:meth:`~bapsflib.lapd.File.read_data`.  The field :code:`'xyz'`
is initialized with :const:`numpy.nan` values, but will be populated if
a control device of :code:`contype = 'motion'` is added (see
:ref:`read_digi_adding_controls`).

------

For details on handling and manipulating :data:`data` see
:ref:`handle_data`.

.. note::

    Since :class:`bapsflib.lapd` leverages the :class:`h5py` package,
    the data in :file:`test.hdf5` resides on disk until one of the read
    methods, :meth:`~bapsflib.lapd.File.read_data`,
    :meth:`~bapsflib.lapd.File.read_msi`, or
    :meth:`~bapsflib.lapd.File.read_controls` is called.  In
    calling on of these methods, the requested data is brought into
    memory as a :class:`numpy.ndarray` and a :class:`numpy.view` onto
    that :data:`ndarray` is returned to the user.

------

.. _read_digi_subset:

Extracting a sub-set
""""""""""""""""""""

.. Sub-setting behavior is determined by three keywords: :data:`index`,
   :data:`shotnum`, and :data:`intersection_set`.

There are three keywords for sub-setting a dataset: :data:`index`,
:data:`shotnum`, and :data:`intersection_set`.  :data:`index` and
:data:`shotnum` are indexing keywords, whereas, :data:`intersection_set`
controls sub-setting behavior between the indexing keywords and the
dataset(s).

:data:`index` refers to the row index of the requested dataset and
:data:`shotnum` refers to the global HDF5 shot number.  Either indexing
keyword can be used, but :data:`index` overrides :data:`shotnum`.
:data:`index` and :data:`shotnum` can be of :func:`type`
:code:`int`, :code:`list(int)`, or :code:`slice()`.  Sub-setting with
:data:`index` looks like::

    >>> # read dataset row 10
    >>> data = f.read_data(board, channel, index=9)
    >>> data['shotnum']
    array([10], dtype=uint32)

    >>> # read dataset rows 10, 20, and 30
    >>> data = f.read_data(board, channel, index=[9, 19, 29])

    >>> # read dataset rows 10 to 19
    >>> data = f.read_data(board, channel, index=slice(9, 19))

    >>> # read every third row in the dataset from row 10 to 19
    >>> data = f.read_data(board, channel, index=slice(9, 19, 3))
    >>> data['shotnum']
    array([10, 13, 16, 19], dtype=uint32)

Sub-setting with :data:`shotnum` looks like::

    >>> # read dataset shot number 10
    >>> data = f.read_data(board, channel, shotnum=10)
    >>> data['shotnum']
    array([10], dtype=uint32)

    >>> # read dataset shot numbers 10, 20, and 30
    >>> data = f.read_data(board, channel, shotnum=[10, 20, 30])

    >>> # read dataset shot numbers 10 to 19
    >>> data = f.read_data(board, channel, shotnum=slice(10, 20))

    >>> # read every 5th dataset shot number from 10 to 19
    >>> data = f.read_data(board, channel, index=slice(10, 20, 5))
    >>> data['shotnum']
    array([10, 15], dtype=uint32)

:data:`intersection_set` modifies what shot numbers are returned by
:meth:`~bapsflib.lapd.File.read_data`.  By default
:code:`intersection_set=True` and forces the returned data to only
correspond to shot numbers that exist in the digitizer dataset, any
specified control device datasets, and those shot numbers represented by
:data:`index` or :data:`shotnum`.  Setting to :code:`False` will return
all shot numbers :code:`>=1` associated with :data:`index` or
:data:`shotnum` and array entries that are not associated with a dataset
will be filled with a "NaN" value (:code:`np.nan` for floats,
:code:`-99999` for integers, and :code:`''` for strings).

.. :data:`intersection_set` modifies what shot numbers are returned by
   :meth:`~bapsflib.lapd.File.read_data`.  If :data:`index` is
   used and no control device datasets are being mated to the digitizer
   dataset, then :data:`intersection_set` has no affect on the returned
   data array.  If :data:`shotnum` is used, then
   :code:`intersection_set=True` (DEFAULT) will ensure that the returned
   data array only contains shot numbers that are specified by
   :code:`shotnum` and are in the digitizer dataset.  If set to
   :code:`False`, then the returned array will contain all shot numbers
   specified by :code:`shotnum` and any shot numbers not found in the
   digitizer dataset will be filled with :code:`numpy.nan` values.

.. _read_digi_digi:

Specifying :code:`digitizer`, :code:`adc`, and :code:`config_name`
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

It is possible for a LaPD generated HDF5 file to contain multiple
digitizers, each of which can have multiple analog-digital-converters
(adc) and multiple configuration settings.  For such a case,
:meth:`~bapsflib.lapd.File.read_data` has the keywords
:data:`digitizer`, :data:`adc`, and :data:`config_name` to direct the
data extraction accordingly.

If :data:`digitizer` is not specified, then it is assumed that the
desired digitizer is the one defined in
:attr:`~bapsflib._hdf.maps.core.HDFMap.main_digitizer`.  Suppose
the :file:`test.hdf5` has two digitizers, :code:`'SIS 3301'` and
:code:`'SIS crate'`.  In this case :code:`'SIS 3301'` would be assumed
as the :attr:`~bapsflib._hdf.maps.core.HDFMap.main_digitizer`.  To
extract data from :code:`'SIS crate'` one would use the
:data:`digitizer` keyword as follows::

    >>> data = f.read_data(board, channel, digitizer='SIS crate')
    >>> data.info['digitizer']
    'SIS crate'

Digitizer :code:`'SIS crate'` can have multiple active
adc's, :code:`'SIS 3302'` and :code:`'SIS 3305'`.  By default, if only
one adc is active then that adc is assumed; however, if multiple adc's
are active, then the adc with the slower clock rate is assumed.
:code:`'SIS 3302'` has the slower clock rate in this case.  To extract
data from :code:`'SIS 3305'` one would use the :data:`adc` keyword as
follows::

    >>> data = f.read_data(board, channel, digitizer='SIS crate',
    >>>                    adc='SIS 3305')
    >>> data.info['adc']
    'SIS 3305'

A digitizer can have multiple configurations, but typically only one
configuration is ever active for the HDF5 file.  In the case that
multiple configurations are active, there is no overlying hierarchy for
assuming one configuration over another.  Suppose digitizer
:code:`'SIS crate'` has two configurations, :code:`'config_01'` and
:code:`'config_02'`.  In this case, one of the configurations has to be
specified at the time of extraction.  To extract data from
:code:`'SIS crate'` under the the configuration :code:`'config_02'` one
would use the :data:`'config_name'` keyword as follows::

    >>> f.file_map.digitizers['SIS crate'].active_configs
    ['config_01', 'config_02']
    >>> data = f.read_data(board, channel, digitizer='SIS crate',
    >>>                    config_name='config_02')
    >>> data.info['configuration name']
    'config_02'

.. _read_digi_adding_controls:

Adding Control Device Data
""""""""""""""""""""""""""

Adding control device data to a digitizer dataset is done with the
keyword :data:`add_controls`.  Specifying :data:`add_controls` will
trigger a call to the
:class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls` class and
extract the desired control device data.
:class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData` then compares and
mates that control device data with the digitizer data according to the
global HDF5 shot number.

:data:`add_controls` must be a list of strings and/or 2-element tuples
specifying the desired control device data to be added to the digitizer
data.  If a control device only controls one configuration, then it is
sufficient to only name that device.  For example, if a
:code:`'6K Compumotor'` is only controlling one probe, then the data
extraction call would look like::

    >>> list(f.file_map.controls['6K Compumotor'].configs)
    [3]
    >>> data = f.read_data(board, channel,
    >>>                    add_controls=['6K Compumotor'])
    >>> data.info['added controls']
    [('6K Compumotor', 3)]

In the case the :code:`'6K Compumotor'` has multiple configurations
(controlling multiple probes), the :data:`add_controls` call must also
provide the configuration name to direct the extraction.  This is done
with a 2-element tuple entry for :data:`add_controls`, where the first
element is the control device name and the second element is the
configuration name.  For the :code:`'6K Compumotor'` the configuration
name is the receptacle number of the probe drive [#]_.  Suppose the
:code:`'6K Compumotor'` is utilizing three probe drives with the
receptacles 2, 3, and 4.  To mate control device data from receptacle 3,
the call would look something like::

    >>> list(f.file_map.controls['6K Compumotor'].configs)
    [2, 3, 4]
    >>> control  = [('6K Compumotor', 3)]
    >>> data = f.read_data(board, channel, add_controls=control)
    >>> data.info['added controls']
    [('6K Compumotor', 3)]

Multiple control device datasets can be added at once, but only
one control device for each control type (:code:`'motion'`,
:code:`'power'`, and :code:`'waveform'`) can be added.  Adding
:code:`'6K Compumotor'` data from receptacle 3 and :code:`'Waveform'`
data would look like::

    >>> list(f.file_map.controls['Waveform'].configs)
    ['config01']
    >>> f.file_map.controls['Waveform'].contype
    'waveform'
    >>> f.file_map.controls['6K Compumotor'].contype
    'motion'
    >>> data = f.read_data(board, channel,
    >>>                    add_controls=[('6K Compumotor', 3),
    >>>                                  'Waveform'])
    >>> data.info['added controls']
    [('6K Compumotor', 3), ('Waveform', 'config01')]

Since :code:`'6K Compumotor'` is a :code:`'motion'` control type it
fills out the :code:`'xyz'` field in the returned numpy structured
array; whereas, :code:`'Waveform'` will add field names to the numpy
structured array according to the fields specified in its mapping
constructor.  See :ref:`read_controls` for details on these added
fields.

.. [#] Control device data can also be independently read using
    :meth:`~bapsflib.lapd.File.read_controls`.
    (see :ref:`read_controls` for usage)
.. [#] Review section :ref:`digi_overview` for how a digitizer is
    organized and configured.
.. [#] Each control device has its own concept of what constitutes a
    configuration. The configuration has be unique to a block of
    recorded data.  For the :code:`'6K Compumotor'` the receptacle
    number is used as the configuration name, whereas, for the
    :code:`'Waveform'` control the configuration name is the name of the
    configuration group inside the :code:`'Waveform` group.  Since the
    configurations are contain in the
    :code:`f.file_map.contorols[con_name].configs` dictionary, the
    configuration name need not be a string.
