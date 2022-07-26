Installation
============

.. Package Requirements
   --------------------


Installing from :code:`pip`
---------------------------

The :mod:`bapsflib` package is registered with
`PyPI <https://pypi.org/project/bapsflib/>`_ and can be installed with
:mod:`pip` via

.. code-block:: bash

    pip install bapsflib

For the most recent development version, :mod:`bapsflib` can be
installed from `GitHub <https://github.com/BaPSF/bapsflib>`_.

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
download), navigate to the main package directory, where the package
:file:`setup.py` file is located, and execute

.. code-block:: bash

    pip install .

or

.. code-block:: bash

    python setup.py install

Useful Installation Links
-------------------------

* bapsflib repository: https://github.com/BaPSF/bapsflib
* bapsflib on PyPI: https://pypi.org/project/bapsflib/
* setuptools documentation: https://setuptools.readthedocs.io/en/latest/index.html
* pip documentation: https://pip.pypa.io/en/stable/
* git installation: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
* cloning and downloading form GitHub: https://help.github.com/articles/cloning-a-repository/
