Architecture
------------

:class:`~bapsflib._hdf.maps.core.HDFMap` takes a modular approach to
mapping a HDF5 file.  It contains a dictionary of known modules with
known layouts.  If one or more of these layouts are discovered inside
the HDF5 file, then the associated mappings are added to the mapping
object.  There are five module categories:

**msi diagnostic**
    This is any sub-group of the :code:`'/MSI/'` group that represents
    a diagnostic device.  A diagnostic device is a probe or sensor that
    records machine state data for every experimental run.

**digitizer**
    This is any group inside the :code:`'/Raw data + config/'` group
    that is associated with a digitizer.  A digitizer is a device that
    records "primary" data; that is, data recorded for a plasma probe.

**control device**
    This is any group inside the :code:`'/Raw data + config/'` group
    that is associated with a device that controls a plasma probe.  The
    recorded data is state data for the plasma probe; for example, probe
    position, bias, driving frequency, etc.

**data run sequence**
    This is the :code:`/Raw data + config/Data run sequence/'` group
    which records the run sequence (operation sequence) of the LaPD DAQ
    controller.

**unknown**
    This is any group or dataset in :code:`'/'`, :code:`'/MSI/'`, or
    :code:`'/Raw data + config/'` groups that is not known by
    :class:`~bapsflib._hdf.maps.core.HDFMap` or is unsuccessfully
    mapped.

Basic Usage
-----------

Basic Structure of :attr:`file_map` Mapping Object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _get_digitizers:

Retrieving Active Digitizers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A list of all detected digitizers can be obtain by doing

    >>> list(f.file_map.digitizers)

The file mappings for all the active digitizers are stored in the
dictionary :code:`f.file_map.digitizers` such that

    >>> list(f.file_map.digitizers.keys())
    Out: list of strings of all active digitizer names

    >>> f.file_map.digitizer[digi_name]
    Out: digitizer mapping object

Retrieving Active Digitizer Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _get_adcs:

Retrieving Active Analog-Digital Converts (adc's) for a Digitizer Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _get_conns:

Retrieving adc Connections and Digitization Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
