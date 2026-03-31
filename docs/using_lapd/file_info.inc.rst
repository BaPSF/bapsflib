Every time a HDF5 file is opened a dictionary of metadata about the file
and the experiment is bound to the file object as
:attr:`~bapsflib.lapd.File.info`.

.. code-block:: python3

    >>> f = lapd.File('test.hdf5')
    >>> f.info
    {'absolute file path': '/foo/bar/test.hdf5',
     'exp description': 'this is an experiment description',
      ...
      'run status': 'Started'}

Table :numref:`f_info_table` lists and describes all the items that can
be found in the info dictionary.

.. _f_info_table:

.. csv-table:: Items in the ``f.info`` dictionary.
               (:attr:`~bapsflib.lapd.File.info`)
    :header: "key", "Description & Equivalence"
    :widths: 20, 60

    ``'absolute file path'``, "
    | absolute path to the HDF5 file
    | ``os.path.abspath(f.filename)``
    "
    ``'exp description'``, "
    | description of experiment
    | ``f['Raw data + config].attrs['Experiment description']``
    "
    ``'exp name'``, "
    | name of the experiment for which the run belongs to
    | ``f['Raw data + config].attrs['Experiment Name']``
    "
    ``'exp set description'``, "
    | description of experiment set
    | ``f['Raw data + config].attrs['Experiment set description']``
    "
    ``'exp set name'``, "
    | name of experiment set the ``'exp name'`` belongs to
    | ``f['Raw data + config].attrs['Experiment set name']``
    "
    ``'file'``, "
    | base name of HDF5 file
    | ``os.path.basename(f.filename)``
    "
    ``'investigator'``, "
    | name of Investigator/PI of the experiment
    | ``f['Raw data + config].attrs['Investigator']``
    "
    ``'lapd version'``,  "
    | LaPD DAQ software version that wrote the HDF5 file
    | ``f.file_map.hdf_version``
    "
    ``'run date'``, "
    | date of experimental run
    | ``f['Raw data + config].attrs['Status date']``
    "
    ``'run description'``, "
    | description of experimental run
    | ``f['Raw data + config].attrs['Description']``
    "
    ``'run name'``, "
    | name of experimental data run
    | ``f['Raw data + config].attrs['Data run']``
    "
    ``'run status'``, "
    | status of experimental run (started, completed, etc.)
    | ``f['Raw data + config].attrs['Status']``
    "
