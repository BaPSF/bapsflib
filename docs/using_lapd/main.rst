.. _using_bapsflib_lapd:

==========================
Using :mod:`bapsflib.lapd`
==========================

The :mod:`bapsflib.lapd` is a one-stop-shop for everything specifically
related to handling data collected on the LaPD.  The package provides:

#. HDF5 file access via :class:`bapsflib.lapd.File`
#. LaPD machine specs and parameters in :mod:`bapsflib.lapd.constants`
#. LaPD specific tools (e.g. port number to LaPD :math:`z` conversion
   :func:`bapsflib.lapd.tools.portnum_to_z`) in
   :mod:`bapsflib.lapd.tools`.

.. contents:: Contents
    :depth: 3
    :local:

Accessing HDF5 Files
====================

.. include:: file_access.inc.rst


LaPD Constants
==============

LaPD Tools
==========
