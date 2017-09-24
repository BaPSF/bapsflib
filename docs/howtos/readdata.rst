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

that are explained in more detail below.

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
