Installation
============

Package Requirements
--------------------


Installing...
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

A copy of :mod:`bapsflib` can be installed into Python's
:file:`site-packages` directory using the :command:`pip3` installer.
Invoking the following command

.. code-block:: bash

    pip3 install git+https://github.com/BaPSF/bapsflib.git#egg=bapsflib

will install the `master` branch of :mod:`bapsflib`.  If an alternate
branch `BranchName` is desired, then invoke:

.. code-block:: bash

    pip3 install git+https://github.com/BaPSF/bapsflib.git@BranchName#egg=bapsflib

Now, the :py:mod:`bapsflib` package can be imported like any other
Python package.

Since :py:mod:`bapsflib` is not currently registered on PyPI, to upgrade
the package the following command has to be used:

.. code-block:: bash

    pip3 install --upgrade git+https://github.com/BaPSF/bapsflib.git#egg=bapsflib

From a Local GitHub Clone
^^^^^^^^^^^^^^^^^^^^^^^^^

The second option is to install from a local copy of the GitHub
repository.  A copy can be made one of two ways, (1) download a copy
directly from the
`GitHub repository <https://github.com/BaPSF/bapsflib>`_ or (2)
make a :command:`git` clone of the repository.  To download a copy go to
the :py:mod:`bapsflib`
`repository <https://github.com/BaPSF/bapsflib>`_, find the
**clone or download** button, choose **Download ZIP**, save to location
of choice, and unpack.  To install the package, navigate to the
:py:mod:`bapsflib` package main directory when the :file:`setup.py` file
is located.  In the terminal excuate the following command:

.. code-block:: bash

    pip3 install .

and this will install the :py:mod:`bapsflib` package in Python's
:file:`site-packages` directory.


Useful Links
------------

* bapsflib repository: https://github.com/BaPSF/bapsflib
* setuptools documentation: https://setuptools.readthedocs.io/en/latest/index.html
* pip documentation: https://pip.pypa.io/en/stable/
* git installation: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
