# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2018 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
import h5py


class FauxSIS3301(h5py.Group):
    """
    Creates a Faux 'SIS 3301' Group in a HDF5 file.
    """

    def __init__(self, id, sn_size=100, nt = 10000, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError('{} is not a GroupID'.format(id))

        # create control group
        gid = h5py.h5g.create(id, b'SIS 3301')
        h5py.Group.__init__(self, gid)

        # define key values
        self._sn_size = sn_size
        self._nt = nt

        # set root attributes
        self._set_sis3301_attrs()

        # build control device sub-groups, datasets, and attributes
        self._update()

    @property
    def nt(self):
        """Number of temporal samples"""
        return self._nt

    @nt.setter
    def nt(self, val):
        """Set the number of temporal samples"""
        if val != self._nt:
            self._nt = val
            self._update()

    @property
    def sn_size(self):
        """Number of shot numbers in a dataset"""
        return self._sn_size

    @sn_size.setter
    def sn_size(self, val):
        """Set the number of shot numbers in a dataset"""
        if val != self._sn_size:
            self._sn_size = val
            self._update()

    def _update(self):
        """
        Updates digitizer group structure (Groups, Datasets, and
        Attributes)
        """
        # clear group before rebuild
        self.clear()

    def _set_sis3301_attrs(self):
        """Sets the 'SIS 3301' group attributes"""
        self.attrs.update({
            'Created date': b'5/21/2004 4:09:05 PM',
            'Description': b'Struck Innovative Systeme 3301 8 channel '
                           b'ADC boards, 100 MHz.  Also provides '
                           b'access to SIS 3820 VME clock distribute.',
            'Device name': b'SIS 3301',
            'Module IP address': b'192.168.7.3',
            'Module VI path': b'C:\\ACQ II home\\Modules\\SIS 3301\\'
                              b'SIS 3301.vi',
            'Type': b'Data acquisition'
        })
