Installation
============

.. Package Requirements
   --------------------


.. Installing...
   -------------

The :py:mod:`bapsflib` package is still in active development so it has
not been registered with PyPI.  Once a stable release is achieve, the
package will be registered and, then, can be directly installed with:

.. code-block:: bash

    pip3 install bapsflib

Directly from GitHub
^^^^^^^^^^^^^^^^^^^^

.. Note::

    Will need a version of :command:`git` installed locally, see
    installation
    `here <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_.

A copy of :py:mod:`bapsflib` can be installed into Python's
:file:`site-packages` directory using the :command:`pip3` installer.  To
install, invoke the following command:

.. code-block:: bash

    pip3 install git+https://https://github.com/rocco8773/bapsflib.git#egg=bapsflib

Now, the :py:mod:`bapsflib` package can be imported like any other
Python package.

Since :py:mod:`bapsflib` is not currently registered on PyPI, to upgrade
the package the following command has to be used:

.. code-block:: bash

    pip3 install --upgrade git+https://https://github.com/rocco8773/bapsflib.git#egg=bapsflib

From a Local GitHub Clone
^^^^^^^^^^^^^^^^^^^^^^^^^

The second option is to install from a local copy of the GitHub
repository.  A copy can be made one of two ways, (1) download a copy
directly from the
`GitHub repository <https://github.com/rocco8773/bapsflib>`_ or (2)
make a :command:`git` clone of the repository.  To download a copy, go
to the :py:mod:`bapsflib`
`repository <https://github.com/rocco8773/bapsflib>`_, find the
**Clone or download** button, choose **Download ZIP**, save to a
location of choice, and unpack.  To install the package, in the
terminal, navigate to the :py:mod:`bapsflib` package main directory
where the :file:`setup.py` file is located and run the following
command:

.. code-block:: bash

    pip3 install .

This will install the :py:mod:`bapsflib` package in Python's
:file:`site-packages` directory.  Like above, the :command:`--upgrade`
argument for :command:`pip3` will not work with this option.

The second method involves making a local clone of the GitHub
repository.  Start in a terminal window, navigate to where the local
:py:mod:`bapsflib` copy will reside, and perform the following command:

.. code-block:: bash

    git clone https://github.com/rocco8773/bapsflib

This will create a clone on your local disk that is under a
:command:`git` version control system (VCS).  This allows the clone to
be easily updated when the GitHub repository is updated.  To do so,
navigate into the :py:mod:`bapsflib` package where the :file:`.git` file
is located.  Using the command

.. code-block:: bash

    git pull

the master branch on the GitHub repository will be merged into the local
clone.  This local clone can be installed into Python's
:file:`site-packages` directory using :command:`pip3 install .`, but
again the :command:`--upgrade` argument will not work with this setup.
Instead, the :py:mod:`bapsflib` package can also be install with and
editable tag

.. code-block:: bash

    pip3 install -e .

which will create a link in Python's path to the local package.  Thus,
any edits to the local copy will immediately be available in the Python
environment.  Thus, updating the package involves performing the command
:command:`git pull` on the local clone.

Useful Links
------------

* bapsflib repository: https://https://github.com/rocco8773/bapsflib
* setuptools documentation: https://setuptools.readthedocs.io/en/latest/index.html
* pip documentation: https://pip.pypa.io/en/stable/
* git installation: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
