=====================
BaPSF HDF5 Data Files
=====================

.. contents::
   :local:

What are HDF5 Data Files?
=========================

BaPSF HDF5 data files store digitized data collected by the experimental plasma devices here at BaPSF. Each file contains information about the data run, the machine state information (MSI) as well as the measurements made by every single diagnostic attached to the Data Acquisition System (DAQ). These files are extremely large and complex to navigate (typically tens to hundreds of GB), requiring data to be stored in a hierachical format in order to quickly access bits of the data with ease. It is for this purpose that the HDF5 file format was chosen to store the data collected from these devices.

What is HDF5?
=============

HDF5 is a technology developed by the
`HDF Group <https://portal.hdfgroup.org/display/support>`_ that is
designed to manage large and complex collections of data, allowing
for advanced relationships between data and user metadata to be
structured through grouping and linking mechanisms.  For HDF5 support,
visit HDF Group's
`HDF5 support site <https://support.hdfgroup.org/HDF5/>`_.

How Data is Acquired and Recorded
=================================

.. include:: hdf5_structure.inc.rst

.. What is a digitizer?
   ====================

.. .. note:: Need to write.

------

.. .. note:: **Things to add**

    .. * explain the what the global HDF5 shot number is
    .. * describe the components of a digitizer, layout the front panel for
          past LaPD digitizers