.. There are three classes of data data saved in a HDF5 file, **digitizer**
   data, **control device** data, and **MSI diagnostic** data (see
   :ref:`lapd_file_overview`).  Each class of data is given its own read
   method on :class:`bapsflib.lapd.File`:

Three classes :class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`,
:class:`~bapsflib._hdf_utils.hdfreadcontrols.HDFReadControls`, and
:class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI` are given to read
data for **digitizers**, **control devices**, and **MSI diagnostics**,
respectively.  Each of these read classes are bound to
:class:`~bapsflib.lapd.File`, see :numref:`f_read_methods`,
and will return a structured :mod:`numpy` array with the requested data.

.. _f_read_methods:

.. csv-table:: Read classes/methods for extracting data from a HDF5 file
    :header: "Read Class", "
        Bound Method on :class:`~bapsflib.lapd.File`", "
        What it does"
    :widths: 10, 15, 40

    :class:`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`, "
    :meth:`~bapsflib.lapd.File.read_data`","
    Designed to extract **digitizer** data from a HDF5 file with the
    option of mating **control device** data at the time of extraction.
    (see reading :ref:`read_digi`)
    "
    :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`, "
    :meth:`~bapsflib.lapd.File.read_controls`", "
    Designed to extract **control device** data. (see reading
    :ref:`read_controls`)
    "
    :mod:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`, "
    :meth:`~bapsflib.lapd.File.read_msi`", "
    Designed to extract **MSI diagnostic** data. (see reading
    :ref:`read_msi`)
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
