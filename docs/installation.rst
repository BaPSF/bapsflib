**************************
Installing :mod:`bapsflib`
**************************

Is :mod:`bapsflib` already installed?
=====================================

Users of ethanol or midas may already have a copy of :mod:`bapsflib` installed in the local library.  To check if the package is installed correctly, import the package and look up the version number:

.. code-block:: bash

    import bapsflib
    bapsflib.__version__

If the package does not exist or if the lastest version is not installed, you may wish to (re)install a copy of the package from an online source such as from `PyPI <https://pypi.org/project/bapsflib/>`_ or
`GitHub <https://github.com/BaPSF/bapsflib>`_.

.. note::
	It is possible for multiple copies of :mod:`bapsflib` to exist on the same computer (e.g. a global copy for all users on the network and a different copy for the local user).  The local copy will take precedence over the global one and users are encouraged to update the local copy for both development and personal use.

Package Requirements
====================

:mod:`bapsflib` requires Python 3.5 or newer to work, and may not be compatible older versions (e.g. Python 2.7).  The following packages are required for installation:

* `NumPy <http://www.numpy.org/>`_ 1.13 or newer
* `SciPy <https://www.scipy.org/>`_ 0.19 or newer
* `Astropy <http://www.astropy.org/>`_ 2.0 or newer

The package also has the following optional dependencies which may be required when running certain features in the package:

* `matplotlib <https://matplotlib.org/>`_ 2.0 or newer
* `h5py <https://www.h5py.org/>`_ 2.8 or newer

How to Install
==============

.. install-pip:

Installing from :code:`pip`
---------------------------

The :mod:`bapsflib` package is registered with `PyPI <https://pypi.org/project/bapsflib/>`_ and can be installed (from the command line) with :mod:`pip` via

.. code-block:: bash

    pip install bapsflib

For the most recent development version, :mod:`bapsflib` can be
installed from `GitHub <https://github.com/BaPSF/bapsflib>`_.

.. install-github-direct:

Installing Directly from GitHub
-------------------------------

To install directly from GitHub, you need to have
`git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_
installed on your computer.  If you do not have :code:`git` installed,
then see `Installing from a GitHub Clone or Download`_.

To install directly from the :code:`master` branch invoke the following
command

.. code-block:: bash

    pip install git+https://github.com/BaPSF/bapsflib.git#egg=bapsflib

If an alternate branch :code:`BranchName` is desired, then invoke

.. code-block:: bash

    pip install git+https://github.com/BaPSF/bapsflib.git@BranchName#egg=bapsflib

.. install-github-clone:

Installing from a GitHub Clone or Download
------------------------------------------

A copy of the :mod:`bapsflib` package can be obtained by
`cloning <https://help.github.com/articles/cloning-a-repository/>`_
or downloading from the GitHub repository.

Cloning the repository requires an installation of :code:`git` on your
computer.  To clone the :code:`master` branch, first, on your computer,
navigate to the directory you want the clone and do

.. code-block:: bash

    git clone https://github.com/BaPSF/bapsflib.git

To download a copy, go to the
`repository <https://github.com/BaPSF/bapsflib>`_, select the branch to
be downloaded, click the green button labeled :ibf:`Clone or download`,
select :ibf:`Download ZIP`, save the zip file to the desired directory,
and unpack.

After getting a copy of the :mod:`bapsflib` package (via clone or
downlaod), navigate to the main package directory, where the package
:file:`setup.py` file is located, and execute

.. code-block:: bash

    pip install .

or

.. code-block:: bash

    python setup.py install

Useful Installation Links
=========================

* bapsflib repository: https://github.com/BaPSF/bapsflib
* bapsflib on PyPI: https://pypi.org/project/bapsflib/
* setuptools documentation: https://setuptools.readthedocs.io/en/latest/index.html
* pip documentation: https://pip.pypa.io/en/stable/
* git installation: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
* cloning and downloading from GitHub: https://help.github.com/articles/cloning-a-repository/