# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License:
#
# TODO: decide on input args for reading out HDF5 data
#

import h5py
import numpy as np


class hdfReadData(np.ndarray):
    """
    I wand self to be the nparray data.
    self should have a meta attribute that contains a dict() of
     metadata for the dataset.
    Metadata that should have:
        'hdf file'       -- HDF5 file name the data was retrieved from
        'dataset name'   -- name of the dataset
        'dataset path'   -- path to said dataset in the HDF5 file
        'crate'          -- crate in which the data was recorded on
        'bit'            -- bit resolution for the crate
        'sample rate'    -- tuple containing the sample rate
                            e.g. (100.0, 'MHz')
        'board'          -- board that the corresponding probe was
                            attached to
                            ~ can I make a 'brd' alias for 'board'
        'channel'        -- channel that the corresponding probe was
                            attached to
                            ~ can I make a 'ch' alias for 'channel'
        'voltage offset' -- voltage offset for the DAQ signal
        'probe name'     -- name of deployed probe...empty dict() item
                            for user to fill out for his/her needs
        'port'           -- 2-element tuple indicating which port the
                            probe was deployed on.
                            e.g. (19, 'W') => deployed on port 19 on the
                            west side of the machine.
                            Second elements descriptors should follow:
                            'T'  = top
                            'TW' = top-west
                            'W'  = west
                            'BW' = bottom-west
                            'B'  = bottom
                            'BE' = bottome-east
                            'E'  = east
                            'TE' = top-east

        Extracting Data
            dset = h5py.get() returns a view of the dataset (dset)
            From there, instantiating from dset will create a copy of
             the data. If you want to keep views then one could use
             dset.values.view().  The dset.vlaues is np.ndarray.
            To extract data, fancy indexing [::] can be used directly on
             dset or dset.values.

    """

    def __new__(cls, hdf_file, board, channel, *args,
                return_view=False, **kwargs):
        # return_view=False -- return a ndarray.view() to save on memory
        #                      when working with multiple datasets...
        #                      this needs to be thought out in more
        #                      detail
        #
        # numpy uses __new__ to initialize objects, so an __init__ is
        # not necessary
        #
        # What I need to do:
        #  1. construct the dataset name
        #     - Required args: board, channel
        #     - Optional kwds: daq, config_name, shots
        #  2. extract view from dataset
        #  3. slice view and assign to obj

        if 'shots' in kwargs.keys():
            shots = kwargs['shots']
        else:
            shots = None

        if 'daq' in kwargs.keys():
            daq = kwargs['daq']
        else:
            daq = None

        if 'config_name' in kwargs.keys():
            config_name = kwargs['config_name']
        else:
            config_name = None

        dname = hdf_file.file_map.construct_dataset_name(
            board, channel, config_name=config_name, daq=daq)
        dpath = hdf_file.file_map.sis_path() + '/' + dname
        dset = hdf_file.get(dpath)

        obj = dset.value.view(cls)
        return obj

    def __array_finalize__(self, obj):
        # according to numpy documentation:
        #  __array__finalize__(self, obj) is called whenever the system
        #  internally allocates a new array from obj, where obj is a
        #  subclass (subtype) of the (big)ndarray. It can be used to
        #  change attributes of self after construction (so as to ensure
        #  a 2-d matrix for example), or to update meta-information from
        #  the “parent.” Subclasses inherit a default implementation of
        #  this method that does nothing.

        # Define meta attribute
        self.info = {'hdf file': None,
                     'dataset name': None,
                     'dataset path': None,
                     'crate': None,
                     'bit': None,
                     'sample rate': None,
                     'board': None,
                     'channel': None,
                     'voltage offset': None,
                     'probe name': None,
                     'port': (None, None)}

    def convert_to_v(self):
        """
        Convert DAQ signal from bits to voltage.
        :return:
        """
        pass

    def convert_to_t(self):
        """
        Convert DAQ signal dependent axis from index to time.
        :return:
        """
        pass

    def dt(self):
        """
        Return timestep dt from the 'sample rate' dict() item.
        :return:
        """
        pass

    def dv(self):
        """
        Return voltage-step from the 'bit' dict() item.
        :return:
        """
        pass

    def full_path(self):
        """
        Return full path of the dataset in the HDF5 file.
        :return:
        """
        pass
