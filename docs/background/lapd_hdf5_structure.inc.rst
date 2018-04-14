.. _fig_HDF5_structure:

.. figure:: images/background__HDF5_structure.png
   :align: center
   :alt: HDF5 internal data structure
   :scale: 65%

   HDF5 internal data structure showing locations of where differing
   LaPD data is stored.

The internal data structure of a HDF5 file looks very similar to a
system file structure (see :numref:`fig_HDF5_structure`), where *groups*
are akin to folders and *datasets* are akin to files.  Data collected by
the LaPD DAQ system is organized into two groups on the root level of
the HDF5 data structure, ``MSI`` and ``Raw data + config``.  The ``MSI``
contains LaPD machine state data, whereas, ``Raw data + config``
contains experimental run data (i.e. anything that is not LaPD machine
state data).  The data that populates these two groups is further
divided into four categories:

1. **MSI diagnostics data**:
       data collected by a device that records a specific machine value
       of the LaPD
2. **Digitizer data**:
       "primary" data recorded by a DAQ digitizer.  "Primary" data is
       any signal that is collected from a plasma probe for the
       experiment.
3. **Control device data**:
       data recorded from a control device that controls some state
       property of the experiment.  This would be state data like probe
       position from a motion control device, probe driving frequency
       from a signal generator, etc.
4. **Data run sequence**
       recorded run sequence (operation sequence) of the LaPD DAQ
       controller

Of which, **MSI diagnostic data** is the only category that is placed
in the ``MSI`` group and the rest are placed in the
``Raw data + config`` gorup (see :numref:`fig_HDF5_structure`).
