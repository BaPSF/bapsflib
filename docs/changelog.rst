=========
Changelog
=========

1.0.1
-----

* Added Control Device mapping modules for:

  * :doc:`NI_XZ <./src/bapsflib._hdf.maps.controls.nixz>` - a probe drive that
    moves a probe in the XZ-plane
    (`PR 22 <https://github.com/BaPSF/bapsflib/pull/22>`_)
  * :doc:`NI_XYZ <./src/bapsflib._hdf.maps.controls.nixyz>` - a probe drive
    that moves a probe withing an XYZ volume
    (`PR 39 <https://github.com/BaPSF/bapsflib/pull/39>`_)

* Update mapping module :mod:`~bapsflib._hdf.maps.digitizers.sis3301` to
  handle variations seen in SmPD generated HDF5 files
  (`PR 30 <https://github.com/BaPSF/bapsflib/pull/30>`_)

* developed decorators :func:`~bapsflib.utils.decorators.with_bf` and
  :func:`~bapsflib.utils.decorators.with_lapdf` to better context manage file
  access to the HDF5 files
  (`PR 23 <https://github.com/BaPSF/bapsflib/pull/23>`_)

  * this allows tests for HDF5 files to run on Windows systems
  * integrated CI `AppVeyor <https://www.appveyor.com/>`_

* Allow function :func:`~bapsflib._hdf.utils.helpers.condition_shotnum` to
  handle single element :mod:`numpy` arrays
  (`PR 41 <https://github.com/BaPSF/bapsflib/pull/41>`_)

* Refactor class
  :class:`~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls` and module
  :mod:`~bapsflib._hdf.utils.hdfreadcontrols` to be plural, which better
  reflects the class behavior and is consistent with the bound method
  :meth:`~bapsflib._hdf.utils.file.File.read_controls` on
  :class:`~bapsflib._hdf.utils.file.File`.
  (`PR 42 <https://github.com/BaPSF/bapsflib/pull/42>`_)

* Setup continuation integration `pep8speaks <https://pep8speaks.com/>`_
  (`PR 43 <https://github.com/BaPSF/bapsflib/pull/43>`_)


1.0.0
-----

* Initial release
