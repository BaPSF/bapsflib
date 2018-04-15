Every time a HDF5 file is opened a dictionary of metadata about the file
and the experiment is bound to the file object as
:attr:`~bapsflib.lapdhdf.files.File.info`.

.. code-block:: python3

    >>> f = lapdhdf.File('test.hdf5')
    >>> f.info
    {'absolute file path': '/foo/bar/test.hdf5',
     'exp description': 'this is an experiment description',
      ...
      'run status': 'Started'}

Table :numref:`f_info_table` lists and describes all the items that can
be found in the info dictionary.

.. _f_info_table:

.. csv-table:: Items in the ``f.info`` dictionary.
               (:attr:`~bapsflib.lapdhdf.files.File.info`)
    :header: "key", "Description & Equivalence"
    :widths: 20, 60

    :code:`'filename'`, "
    | name of HDF5 file
    | :code:`os.path.split(f.filename)[-1]`
    "
    :code:`'absolute file path'`, "
    | absolute path to the HDF5 file
    | :code:`os.path.abspath(f.filename)`
    "
    :code:`'lapd version'`,  "
    | LaPD DAQ software version that wrote the HDF5 file
    | :code:`f.file_map.hdf_version`
    "
    :code:`'run name'`, "
    | name of experimental data run
    | :code:`f['Raw data + config].attrs['Data run']`
    "
    :code:`'run description'`, "
    | description of experimental run
    | :code:`f['Raw data + config].attrs['Description']`
    "
    :code:`'run status'`, "
    | status of experimental run (started, completed, etc.)
    | :code:`f['Raw data + config].attrs['Status']`
    "
    :code:`'run date'`, "
    | date of experimental run
    | :code:`f['Raw data + config].attrs['Status date']`
    "
    :code:`'investigator'`, "
    | name of Investigator/PI of the experiment
    | :code:`f['Raw data + config].attrs['Investigator']`
    "
    :code:`'exp name'`, "
    | name of the experiment in which the run of the HDF5 file resides
    | :code:`f['Raw data + config].attrs['Experiment Name']`
    "
    :code:`'exp description'`, "
    | description of experiment
    | :code:`f['Raw data + config].attrs['Experiment description']`
    "
    :code:`'exp set name'`, "
    | name of experiment set the ``'exp name'`` resides
    | :code:`f['Raw data + config].attrs['Experiment set name']`
    "
    :code:`'exp set description'`, "
    | description of experiment set
    | :code:`f['Raw data + config].attrs['Experiment set description']`
    "