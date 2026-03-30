.. py:currentmodule:: bapsflib.lapd

Digitizer data is read using the
:meth:`~bapsflib.lapd._hdf.file.File.read_data` method on
:class:`~bapsflib.lapd._hdf.file.File`.  The method also has the option
of mating control device data at the time of declaration (see section
:ref:`read_digi_adding_controls`) [#]_.

At a minimum, the :meth:`~bapsflib.lapd._hdf.file.File.read_data` method
only needs a board number and channel number to extract data.  For
example, the entire dataset for a signal attached to ``board=1`` and
``channel=0`` can be extracted as follows:

.. code-block:: python3

    >>> import numpy as np
    >>> from bapsflib import lapd
    >>> from bapsflib._hdf.utils.hdfreaddata import HDFReadData
    >>>
    >>> f = lapd.File('test.hdf5')
    >>> board, channel = 1, 0
    >>> data = f.read_data(board, channel)
    >>>
    >>> isinstance(data, HDFReadData)
    True
    >>> isinstance(data, np.ndarray)
    True

where ``data`` is an instance of
:class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`, which is a
subclass of `numpy.ndarray`.  Thus, ``data`` behaves just like
a :class:`numpy.ndarray`, but has additional BaPSF focused
methods/attributes that describe the data's origin and parameters
(see :numref:`table_HDFReadData_methods`).

.. _table_HDFReadData_methods:

.. csv-table:: Useful methods on
               :class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`
    :header: "Method", "Description"
    :widths: 5, 40

    :attr:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData.dt`, "
    temporal step size (in sec) adjusted for the adc clock rate and
    sample averaging
    "
    :attr:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData.dv`, "
    voltage step size (in volts) calculated from the adc's
    bit-resolution and voltage range
    "
    :attr:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData.info`, "
    dictionary of meta-data corresponding to the origin of the
    extracted data
    "

By default, ``data`` is a structured `numpy` array with the
following `~numpy.dtype`::

    >>> data.dtype
    dtype([('shotnum', '<u4'),
           ('signal', '<f4', (12288,)),
           ('xyz', '<f4', (3,))])

where ``'shotnum'`` contains the HDF5 shot number, ``'signal'``
contains the signal recorded by the digitizer, and ``'xyz'`` is a
3-element array containing the probe position.  In this example,
the digitized signal is automatically converted from bits to voltage
and ``12288`` is the size of the signal's time-array.  The
``'xyz'`` is initialized with `numpy.nan` values, unless
motion control data is requested at instantiation (see
:ref:`read_digi_adding_controls`).

There are several additional keyword options to control the read
behavior of :meth:`~bapsflib.lapd._hdf.file.File.read_data`:

.. csv-table:: Optional keywords for
               :meth:`~bapsflib.lapd._hdf.file.File.read_data`
    :header: "Keyword", "Default", "Description"
    :widths: 10, 5, 40

    ``index``, ``slice(None)``, "row index of the HDF5 dataset
    (see :ref:`read_digi_subset`)
    "
    "``shotnum``", "``slice(None)``", "global HDF5 file shot
    number (see :ref:`read_digi_subset`)
    "
    ``digitizer``, `None`, "
    | digitizer name for which ``board`` and ``channel`` belong
      to
    | (see :ref:`read_digi_digi`)
    "
    ``adc``, `None` , "
    | name of the digitizer's analog-digital-converter (adc) for which
      ``board`` and ``channel`` belong to
    | (see :ref:`read_digi_digi`)
    "
    ``config_name``, `None`, "
    | name of the digitizer configuration
    | (see :ref:`read_digi_digi`)
    "
    ``keep_bits``, `False`, "Set `True` to return the
    digitizer data in bit values. By default the digitizer data is
    converted to voltage.
    "
    ``add_controls``, `None`, "
    | list of control devices whose data will be matched and added to
      the requested digitizer data
    | (see :ref:`read_digi_adding_controls`
    "
    ``intersection_set``, `True`, "
    | Ensures that the returned data array only contains shot numbers
      that are inclusive in ``shotnum``, the digitizer dataset, and
      all control device datasets.
    | (see :ref:`read_digi_subset`)
    "
    ``silent``, `False`, "set `True` to suppress
    `bapsflib` generated warnings
    "

------

For details on handling and manipulating ``data`` see
:ref:`handle_data`.

.. note::

    Since :class:`bapsflib.lapd` leverages the :class:`h5py` package,
    the data in the HDF5 file resides on disk until one of the read
    methods, :meth:`~bapsflib.lapd._hdf.file.File.read_data`,
    :meth:`~bapsflib.lapd._hdf.file.File.read_msi`, or
    :meth:`~bapsflib.lapd._hdf.file.File.read_controls` is called.  In
    calling one of these methods, the requested data is brought into
    memory as a :class:`numpy.ndarray` and a :class:`numpy.view` onto
    that `~numpy.ndarray` is returned to the user.

------

.. _read_digi_subset:

Extracting a sub-set
''''''''''''''''''''

.. Sub-setting behavior is determined by three keywords: ``index``,
   ``shotnum``, and ``intersection_set``.

There are three keywords for sub-setting a dataset: ``index``,
``shotnum``, and ``intersection_set``.  ``index`` and ``shotnum`` are
indexing keywords, whereas, ``intersection_set`` controls sub-setting
behavior between the indexing keywords and the dataset(s).

``index`` refers to the row index of the requested dataset and
``shotnum`` refers to the global HDF5 shot number.  Either indexing
keywords can be used, but ``shotnum`` overrides ``index``.  However,
there is extra overhead in determining the ``shotnum`` dataset
locations, so ``index`` will often execute quicker than, or at least on
par with, ``shotnum``.  ``index`` and ``shotnum`` can be of type `int`,
 ``List[int]``, `slice`, `numpy.ndarray`, or `numpy.s_`.

Sub-setting with ``index`` looks like::

    >>> import numpy as np

    >>> # -- Using int values --
    >>> # read dataset row 10
    >>> data = f.read_data(board, channel, index=9)
    >>> data['shotnum']
    HDFReadData([10], dtype=uint32)

    >>> # -- using List[int] or numpy.ndarray values --
    >>> # read dataset rows 10, 20, and 30
    >>> data = f.read_data(board, channel, index=[9, 19, 29])
    >>> data = f.read_data(board, channel, index=np.array([9, 19, 29]))

    >>> # -- Using slice() or numpy.s_ --
    >>> # read dataset rows 10 to 19
    >>> data = f.read_data(board, channel, index=slice(9, 19))
    >>> data = f.read_data(board, channel, index=np.s_[9:19])

    >>> # read every third row in the dataset from row 10 to 19
    >>> data = f.read_data(board, channel, index=slice(9, 19, 3))
    >>> data = f.read_data(board, channel, index=np.s_[9:19:3])
    >>> data['shotnum']
    HDFReadData([10, 13, 16, 19], dtype=uint32)

Sub-setting with ``shotnum`` looks like::

    >>> import numpy as np

    >>> # -- Using int values --
    >>> # read dataset shot number 10
    >>> data = f.read_data(board, channel, shotnum=10)
    >>> data['shotnum']
    HDFReadData([10], dtype=uint32)

    >>> # -- using List[int] or numpy.ndarray values --
    >>> # read dataset shot numbers 10, 20, and 30
    >>> data = f.read_data(board, channel, shotnum=[10, 20, 30])
    >>> data = f.read_data(board, channel, shotnum=np.array([10, 20, 30]))

    >>> # -- Using slice() or numpy.s_ --
    >>> # read dataset shot numbers 10 to 19
    >>> data = f.read_data(board, channel, shotnum=slice(10, 20))
    >>> data = f.read_data(board, channel, shotnum=np.s_[10:20])

    >>> # read every 5th dataset shot number from 10 to 19
    >>> data = f.read_data(board, channel, index=slice(10, 20, 5))
    >>> data = f.read_data(board, channel, index=np.s_[10:20:5])
    >>> data['shotnum']
    HDFReadData([10, 15], dtype=uint32)

``intersection_set`` modifies what shot numbers are returned by
:meth:`~bapsflib.lapd._hdf.file.File.read_data`.  By default
``intersection_set=True`` which forces the returned data to only contain
shot numbers that exist in the digitizer dataset, exist in any specified
control device datasets, and are requested by ``index`` or ``shotnum``.
Setting ``intersection_set`` to `False` will return a ``data`` array
that has all shot numbers (:math:`\ge 1`) specified by ``index`` or
``shotnum``. If a digitizer or control device dataset does not have an
entry corresponding to a specific shot number, then its spot in the
data array will be filled with a "NaN" value (`numpy.nan` for floats,
``-99999`` for signed-integers, and `numpy.empty` for any other
`numpy.dtype`).

.. _read_digi_digi:

Specifying ``digitizer``, ``adc``, and ``config_name``
''''''''''''''''''''''''''''''''''''''''''''''''''''''

It is possible for a LaPD generated HDF5 file to contain multiple
digitizers, each of which can have multiple analog-digital-converters
(adc's) and multiple configuration settings.  For such a case,
:meth:`~bapsflib.lapd._hdf.file.File.read_data` has the keywords
``digitizer``, ``adc``, and ``config_name`` to direct the
data extraction accordingly.

If ``digitizer`` is not specified, then it is assumed that the desired
digitizer is the one defined in
:attr:`~bapsflib._hdf.maps.mapper.HDFMapper.main_digitizer`.  Suppose
the :file:`test.hdf5` has two digitizers, ``'SIS 3301'`` and
``'SIS crate'``, then ``'SIS 3301'`` would be assumed as the
:attr:`~bapsflib._hdf.maps.mapper.HDFMapper.main_digitizer`.  To
extract data from ``'SIS crate'`` one would use the ``digitizer``
keyword as follows::

    >>> data = f.read_data(board, channel, digitizer='SIS crate')
    >>> data.info['digitizer']
    'SIS crate'

Digitizer ``'SIS crate'`` can have multiple active adc's, ``'SIS 3302'``
and ``'SIS 3305'``.  By default, if only one adc is active then that adc
is assumed; however, if multiple adc's are active, then the adc with the
slower clock rate is assumed.  ``'SIS 3302'`` has the slower clock rate
in this case, so to extract data from ``'SIS 3305'`` one would use the
``adc`` keyword as follows::

    >>> data = f.read_data(board, channel, digitizer='SIS crate',
    ...                    adc='SIS 3305')
    >>> data.info['adc']
    'SIS 3305'

A digitizer can also have multiple configurations, but typically only
one configuration is ever active for the HDF5 file.  In the case that
multiple configurations are active, there is no overlying hierarchy for
assuming one configuration over another.  Suppose digitizer
``'SIS crate'`` has two configurations, ``'config_01'`` and
``'config_02'``.  In this case, one of the configurations has to be
specified at the time of extraction.  To extract data from
``'SIS crate'`` under the the configuration ``'config_02'`` one
would use the ``config_name`` keyword as follows::

    >>> f.digitizers['SIS crate'].active_configs
    ['config_01', 'config_02']
    >>> data = f.read_data(board, channel, digitizer='SIS crate',
    ...                    config_name='config_02')
    >>> data.info['configuration name']
    'config_02'

.. _read_digi_adding_controls:

Adding Control Device Data
''''''''''''''''''''''''''

Adding control device data to a digitizer dataset is done with the
keyword ``add_controls``.  Specifying ``add_controls`` will trigger a
call to the
:class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls` class and
extract the desired control device data.
:class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData` then compares and
mates that control device data with the digitizer data according to the
global HDF5 shot number.

``add_controls`` must be a list of strings and/or 2-element tuples
specifying the desired control device data to be added to the digitizer
data.  If a control device only controls one configuration, then it is
sufficient to only name that device.  For example, if the
``'6K Compumotor'`` motion control device is only driving one
probe, then the data extraction call would look like::

    >>> list(f.controls['6K Compumotor'].configs)
    [3]
    >>> data = f.read_data(board, channel,
    ...                    add_controls=['6K Compumotor'])
    >>> data.info['added controls']
    [('6K Compumotor', 3)]

In the case the ``'6K Compumotor'`` control device has multiple
configurations (driving multiple probes), the ``add_controls`` call
must also provide the configuration name to direct the extraction.
This is done with a 2-element tuple entry for ``add_controls``,
where the first element is the control device name and the second
element is the configuration name.  For the ``'6K Compumotor'`` the
configuration name is the receptacle number of the probe drive [#]_.
Suppose the ``'6K Compumotor'`` is utilizing three probe drives
with the receptacles 2, 3, and 4.  To mate control device data from
receptacle 3, the call would look something like::

    >>> list(f.controls['6K Compumotor'].configs)
    [2, 3, 4]
    >>> control  = [('6K Compumotor', 3)]
    >>> data = f.read_data(board, channel, add_controls=control)
    >>> data.info['added controls']
    [('6K Compumotor', 3)]

Multiple control device datasets can be added at once, but only
one control device for each control type can be added (see
:class:`~bapsflib._hdf.ConType` for control types).  Adding
``'6K Compumotor'`` data from receptacle 3 and ``'Waveform'``
data would look like::

    >>> list(f.controls['Waveform'].configs)
    ['config01']
    >>> f.controls['Waveform'].contype
    contype.waveform
    >>> f.controls['6K Compumotor'].contype
    contype.motion
    >>> data = f.read_data(board, channel,
    >>>                    add_controls=[('6K Compumotor', 3),
    >>>                                  'Waveform'])
    >>> data.info['added controls']
    [('6K Compumotor', 3), ('Waveform', 'config01')]

    >>> data.dtype
    dtype([('shotnum', '<u4'),
           ('signal', '<f4', (12288,)),
           ('xyz', '<f4', (3,)),
           ('command', '<U150')])

Since ``'6K Compumotor'`` is a :attr:`~bapsflib._hdf.ConType.motion`
control type, it fills out the ``'xyz'`` field in the returned
data array; whereas, ``'Waveform'`` will add field names to the
data array according to the fields specified in its mapping
constructor
:class:`~bapsflib._hdf.maps.controls.waveform.HDFMapControlWaveform`.
See :ref:`read_controls` for details on these added fields.

.. [#] Control device data can also be independently read using
    :meth:`~bapsflib.lapd.File.read_controls`.
    (see :ref:`read_controls` for usage)

.. [#] Each control device has its own concept of what constitutes a
    configuration. The configuration has to be unique to a block of
    recorded data.  For the ``'6K Compumotor'`` the receptacle number is
    used as the configuration name, whereas, for the ``'Waveform'``
    control the configuration name is the name of the configuration
    group inside the ``'Waveform'`` group.  Since the configurations are
    contain in the ``f.file_map.controls[config_name].configs``
    dictionary, the configuration name need not be a string.
