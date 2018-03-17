There are three classes of data data saved in a HDF5 file, **digitizer**
data, **control device** data, and **MSI diagnostic** data (see
:ref:`lapd_file_overview`).  Each class of data is given its own read
method on :class:`bapsflib.lapdhdf.File`:

.. csv-table::
    :header: "Method", "What it does"
    :widths: 10, 40

    :meth:`~bapsflib.lapdhdf.files.File.read_data`, "Designed to extract
    **digitizer** data from a HDF5 file with the option of mating
    **control device** data at the time of extraction. (see
    :ref:`read_digi`)
    "
    :meth:`~bapsflib.lapdhdf.files.File.read_controls`, "Designed to
    extract **control device** data. (see :ref:`read_controls`)
    "
    :meth:`~bapsflib.lapdhdf.files.File.read_msi`, "Designed to extract
    **MSI diagnostic** data. (see :ref:`read_msi`)
    "

.. _read_digi:

For a Digitizer
^^^^^^^^^^^^^^^^

.. include:: read_from_digi.inc.rst

.. _read_controls:

For Control Devices
^^^^^^^^^^^^^^^^^^^

.. note:: To be written

.. _read_msi:

For a MSI Diagnostic
^^^^^^^^^^^^^^^^^^^^

.. include:: read_from_msi.inc.rst
