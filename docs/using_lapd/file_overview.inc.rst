The :class:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview` class provides a
set of tools (see :numref:`f_overview_methods`) to report the results of
the HDF5 file mapping by :class:`~bapsflib._hdf.maps.core.HDFMap`.
An instance of :class:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview` is
bound to :class:`~bapsflib.lapd.File` as the
:attr:`~bapsflib.lapd.File.overview` attribute and will report
the current status of the mapping object.

.. code-block:: python3

    >>> f = lapd.File('test.hdf5')
    >>> f.overview
    <bapsflib.lapd._hdf.hdfoverview.hdfOverview>

Thus, if any changes
are made to the mapping object
(:attr:`~bapsflib.lapd.File.file_map`), which could happen for
certain control devices [*]_, then those changes will be reflected in the
overview report.


The overview report is divided into three blocks:

    #. General File and Experimental Info
        * This block contains information on the file (name, path, etc.),
          the experiment (exp. name, investigator, etc.), and the
          experimental run setup (run name, description, etc.).
        * Example:

          .. include:: ./file_overview__sample_general.inc.rst

    #. Discovery Report
        * This block gives a brief report on what devices the
          :class:`~bapsflib._hdf.maps.core.HDFMap` class discovered
          in the the file.
        * There are no details about each discovered device, just what
          was discovered.
        * Example:

          .. include:: ./file_overview__sample_brief.inc.rst

    #. Detailed Report
        * This block reports details on the mapping results for each
          discovered device (MSI diagnostics, control devices, and
          digitizers).
        * Basically reports the constructed ``configs`` dictionary of
          each devices mapping object.
        * Example:

          .. include:: ./file_overview__sample_detailed.inc.rst


The methods provided by
:class:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview` (see
:numref:`f_overview_methods`) allow for printing and saving of the
complete overview, as well as, printing the individual blocks or
sections of the blocks.

.. _f_overview_methods:

.. csv-table:: "Methods provided by
               :class:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview`
               for reporting a HDF5 file overview"
    :header: "Method", "Description and Call"
    :widths: 15, 60

    :meth:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview.print`, "
    Print to screen the entire overview.

    >>> f.overview.print()
    "
    :meth:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview.save`, "
    Save the report to a file given by ``filename``.

    >>> f.overview.save(filename)

    |

    If :code:`filename=True`, then a text file is created with the same
    name as the HDF5 file in the same location.

    >>> f.overview.save(True)
    "
    :meth:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview.report_general`, "
    Print the general info block.

    >>> f.overview.report_general()
    "
    :meth:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview.report_discovery`, "
    Print the discovery report block.

    >>> f.overview.report_discovery()
    "
    :meth:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview.report_details`, "
    Print the detail report block.

    >>> f.overview.report_details()
    "
    :meth:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview.report_controls`, "
    Print the detail report block for all control devices.

    >>> f.overview.report_controls()

    |

    Print the detail report block for a specific control device
    (e.g. **Waveform**).

    >>> f.overview.report_controls(name='Waveform')
    "
    :meth:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview.report_digitizers`, "
    Print the detail report block for all digitizers.

    >>> f.overview.report_digitizers()

    |

    Print the detail report block for a specific digitizer
    (e.g. **SIS 3301**).

    >>> f.overview.report_digtitizers(name='SIS 3301')
    "
    :meth:`~bapsflib.lapd._hdf.hdfoverview.hdfOverview.report_msi`, "
    Print the detail report block for all MSI diagnostics.

    >>> f.overview.report_msi()

    |

    Print the detail report block for a specific MSI diagnostic
    (e.g. **Discharge**).

    >>> f.overview.report_msi(name='Discharge')
    "

.. [*] the mapping configuration for command list focused control
    devices can be modified when the command list is parsed (
    :red:`provide a link to command list control device section here once written`)
