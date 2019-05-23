# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2019 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
import h5py
import math
import numpy as np
import random

from warnings import warn


class FauxNIXYZ(h5py.Group):
    """
    Creates a Faux 'NI_XYZ' control group in the HDF5 file.
    """

    class Knobs(object):
        """
        A class that contains all the controls for specifying the
        digitizer group structure.
        """
        def __init__(self, faux, n_motionlists, sn_size):
            super().__init__()
            self._faux = faux

            # initialize knobs
            self._n_configs = 1
            self._n_probes = 1
            self.n_motionlists = n_motionlists
            self.sn_size = sn_size

        @property
        def n_configs(self):
            """Number of NI_XYZ configurations"""
            # return self._faux.n_configs
            return self._n_configs

        @property
        def n_motionlists(self):
            """Number of motion lists"""
            return self._n_motionlists

        @n_motionlists.setter
        def n_motionlists(self, val: int):
            """Set number of motion lists"""
            # check if self._n_motionlists has been defined
            if hasattr(self, '_n_motionlists'):
                old_val = self._n_motionlists
            else:
                old_val = 1

            # condition val
            if not isinstance(val, (int, np.integer)):
                warn("Setting value must be an integer of >=1")
                val = old_val
            elif val < 1:
                warn("Setting value must be an integer of >=1")
                val = old_val

            # only update if self._n_motionlists had been defined once
            # prior
            if hasattr(self, '_n_motionlists'):
                self._n_motionlists = val
                self._faux.populate()
            else:
                self._n_motionlists = val

        @property
        def n_probes(self):
            """Number of controlled probes"""
            # return self._faux.n_probes
            return self._n_probes

        @property
        def sn_size(self):
            """Shot number size"""
            return self._sn_size

        @sn_size.setter
        def sn_size(self, val: int):
            """Set shot number size"""
            # check if self._sn_size has been defined
            if hasattr(self, '_sn_size'):
                old_val = self._sn_size
            else:
                old_val = 100

            # condition val
            if not isinstance(val, (int, np.integer)):
                warn("Setting value must be an integer of >=1")
                val = old_val
            elif val < 1:
                warn("Setting value must be an integer of >=1")
                val = old_val

            # only update if self._sn_size had been defined once prior
            if hasattr(self, '_sn_size'):
                self._sn_size = val
                self._faux.populate()
            else:
                self._sn_size = val

        def reset(self):
            """Reset to defaults"""
            self._n_configs = 1
            self._n_probes = 1
            self._n_motionlists = 1
            self._sn_size = 100
            self._faux.populate()

    def __init__(self, id, n_motionlists=1, sn_size=100, **kwargs):
        # ensure id is for a HDF5 group
        if not isinstance(id, h5py.h5g.GroupID):
            raise ValueError('{} is not a GroupID'.format(id))

        # create control group
        gid = h5py.h5g.create(id, b'NI_XYZ')
        h5py.Group.__init__(self, gid)

        # store number on configurations
        self._knobs = self.Knobs(self, n_motionlists, sn_size)
        
        # initialize some attributes
        self._ml = []  # list of motion lists
        self.configs = {}  # configurations dictionary
        
        # set root attributes
        self._set_xyz_attrs()

        # build control device sub-groups, datasets, and attributes
        self.populate()

    def _add_dataset(self):
        """Create dataset"""
        # create numpy array
        dset_name = 'Run time list'
        shape = (self.knobs.sn_size, )
        dtype = np.dtype([
            ('Shot number', np.int32),
            ('Configuration name', np.bytes_, 120),
            ('motion_index', np.int32),
            ('x', np.float64),
            ('y', np.float64),
            ('z', np.float64),
            ('r', np.float64),
            ('phi', np.float64),
            ('theta', np.float64),
        ])
        data = np.ndarray(shape=shape, dtype=dtype)

        # assign shot numbers
        data['Shot number'] = \
            np.arange(1, shape[0] + 1, 1,
                      dtype=data.dtype['Shot number'].type)

        # assign motion lists (aka 'Configuration name')
        # assign motion_index
        start = 0
        for ml in self._ml:
            # determine stop index
            stop = start + ml['size']

            # insert values
            data['Configuration name'][start:stop:1] = ml['name']
            data['motion_index'][start:stop:1] = \
                np.arange(0, ml['size'], 1,
                          dtype=data.dtype['motion_index'].type)

            # move start index
            start = stop

        # fill position fields
        # TODO: create a real fill, opposed to zeros
        #
        data['x'].fill(0.0)
        data['y'].fill(1.0)
        data['z'].fill(2.0)
        data['r'].fill(3.0)
        data['phi'].fill(np.pi/10.0)
        data['theta'].fill(np.pi/20.0)

        # create dataset
        self.create_dataset(dset_name, data=data)

        # add to configs
        self.configs['config01']['dset name'] = dset_name

    def _add_motionlist_groups(self):
        """Add motion list groups"""
        # determine possible data point arrangements for motion lists
        # 1. find divisible numbers of sn_size
        # 2. find (Nx, Ny, Nz) combos for each dataset
        sn_size_for_ml = []
        NN = []
        if self.knobs.n_motionlists == 1:
            # set shot number size per for each motion list
            sn_size_for_ml.append(self.knobs.sn_size)
        else:
            # set shot number size per for each motion list
            sn_per_ml = int(math.floor(
                self.knobs.sn_size / self.knobs.n_motionlists))
            sn_remainder = (self.knobs.sn_size
                            - ((self.knobs.n_motionlists - 1)
                               * sn_per_ml))
            sn_size_for_ml.extend([sn_per_ml]
                                  * (self.knobs.n_motionlists - 1))
            sn_size_for_ml.append(sn_remainder)

        # build NN of each motion list
        # NN = [(Nx, Ny, Nz), ...]
        # Nx * Ny * Nz = number of shot numbers used for ML
        for i in range(self.knobs.n_motionlists):
            # find divisible numbers
            sn_div = []
            for j in range(sn_size_for_ml[i]):
                if sn_size_for_ml[i] % (j + 1) == 0:
                    sn_div.append(j + 1)

            # define Nx
            sn_div_index = random.randint(0, len(sn_div) - 1)
            Nx = sn_div[sn_div_index]

            # define Ny
            sn_div.clear()
            sn_left = int(sn_size_for_ml[i] / Nx)
            for j in range(sn_left):
                if sn_left % (j + 1) == 0:
                    sn_div.append(j + 1)
            sn_div_index = random.randint(0, len(sn_div) - 1)
            Ny = sn_div[sn_div_index]

            # define Nz
            Nz = int(sn_left / Ny)
            NN.append((Nx, Ny, Nz))

        # add motionlist sub-groups
        # - define motionlist names
        # - create motionlist group
        # - define motionlist group attributes
        for i in range(self.knobs.n_motionlists):
            # define motionlist name
            ml_name = 'ml-{:04}'.format(i + 1)
            self._ml.append({'name': ml_name,
                             'size': sn_size_for_ml[i]})

            # create motionlist group
            ml_gname = ml_name
            self.create_group(ml_gname)

            # set motionlist attributes
            self[ml_gname].attrs.update({
                'z_port': np.float64(35.0),
                'x0': np.float64(0.0),
                'Nx': np.float64(NN[i][0]),
                'dx': np.float64(0.5),
                'y0': np.float64(0.0),
                'Ny': np.float64(NN[i][1]),
                'dy': np.float64(0.5),
                'z0': np.float64(0.0),
                'Nz': np.float64(NN[i][2]),
                'dz': np.float64(0.5),
                'fan_XYZ':
                    np.bytes_('FALSE') if bool(i % 2)
                    else np.bytes_('TRUE'),
                'min_zdrive_steps': np.float64(-2000000),
                'max_zdrive_steps': np.float64(2000000),
                'min_ydrive_steps': np.float64(-2469350),
                'max_ydrive_steps': np.float64(2546296),
                'probe_name': np.bytes_('probe1'),
            })

        # fill configs dict
        # there's one config and all ml's are in it
        for config_name in self.configs:
            self.configs[config_name]['motion lists'] = \
                [self._ml[i]['name']
                 for i in range(self.knobs.n_motionlists)]

    def _set_xyz_attrs(self):
        """Set the 'NI_XYZ' group attributes"""
        self.attrs.update({
            'Device name': np.bytes_('NI_XYZ'),
            'Type': np.bytes_('Experimental control'),
            'Description': np.bytes_(
                '3D Drive from SMPD using National Instruments '
                'ethernet motors (repackaged Applied Motion '
                'Systems drives)'),
            'Module IP address': np.bytes_('192.168.7.76'),
            'Module VI path': np.bytes_('Modules\\NI_XYZ\\NI_XYZ.vi'),
            'Created data': np.bytes_('9/9/2018 2:49:51 PM'),
        })

    @property
    def knobs(self):
        """Knobs for controlling structure of device group"""
        return self._knobs

    def populate(self):
        """
        Updates the control group structure (Groups, Datasets, and
        Attributes)
        """
        # clear group before rebuild
        self.clear()

        # re-initialize key lists
        self._ml.clear()

        # re-initialize key dicts
        self.configs.clear()
        self.configs['config01'] = {}

        # add sub-groups
        self._add_motionlist_groups()

        # add datasets
        self._add_dataset()
