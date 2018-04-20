.. code-block:: none

    Detailed Reports
    -----------------


    Digitizer Report
    ^^^^^^^^^^^^^^^^

    SIS crate (main)
    +-- adc's:  ['SIS 3302', 'SIS 3305']
    +-- Configurations Detected (1)                               (1 active, 0 inactive)
    |   +-- sis0-10ch                                             active
    |   |   +-- adc's (active):  ['SIS 3302']
    |   |   +-- path: /Raw data + config/SIS crate/sis0-10ch
    |   |   +-- SIS 3302 adc connections
    |   |   |   |   +-- (brd, [ch, ...])               bit  clock rate   nshotnum  nt        shot ave.  sample ave.
    |   |   |   |   +-- (1, [3, 4, 5, 6, 7, 8])        16   100.0 MHz    6160      12288     None       8
    |   |   |   |   +-- (2, [1, 2, 3, 4])              16   100.0 MHz    6160      12288     None       8

    Control Device Report
    ^^^^^^^^^^^^^^^^^^^^^

    Waveform
    +-- path:     /Raw data + config/Waveform
    +-- contype:  waveform
    +-- Configurations Detected (1)
    |   +-- waveform_50to150kHz_df10kHz_nf11
    |   |   +-- {...}

    MSI Diagnostic Report
    ^^^^^^^^^^^^^^^^^^^^^

    Discharge
    +-- path:  /MSI/Discharge
    +-- configs
    |   +--- {...}
    Gas pressure
    +-- path:  /MSI/Gas pressure
    +-- configs
    |   +-- {...}
    Heater
    +-- path:  /MSI/Heater
    +-- configs
    |   +-- {...}
    Interferometer array
    +-- path:  /MSI/Interferometer array
    +-- configs
    |   +-- {...}
    Magnetic field
    +-- path:  /MSI/Magnetic field
    +-- configs
    |   +-- {...}
