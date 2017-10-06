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


# from .. import lapdhdf
# from .hdferrors import *


class hdfReadData(np.recarray):
    """
    Reads the data out of the HDF5 file:

    .. py:data:: info

        A dictionary container of metadata for the extracted data. The
        dict() keys are:

        .. list-table::
            :widths: 5 3 11

            * - :py:const:`hdf file`
              - `str`
              - HDF5 file name the data was retrieved from
            * - :py:const:`dataset name`
              - `str`
              - name of the dataset
            * - :py:const:`dataset path`
              - `str`
              - path to said dataset in the HDF5 file
            * - :py:const:`digitizer`
              - `str`
              - digitizer group name
            * - :py:const:`adc`
              - `str`
              - analog-digital converter in which the data was recorded
                on
            * - :py:const:`bit`
              - `int`
              - bit resolution for the adc
            * - :py:const:`sample rate`
              - (`int`, `float`)
              - tuple containing sample rate, e.g. (100.0, 'MHz')
            * - :py:const:`board`
              - `int`
              - board that the probe was connected to
            * - :py:const:`channel`
              - `int`
              - channel of the board that the probe was connected to
            * - :py:const:`voltage offset`
              - `float`
              - voltage offset of the digitized signal
            * - :py:const:`probe name`
              - `str`
              - name of deployed probe...empty for user to use at
                his/her discretion
            * - :py:const:`port`
              - (`int`, `str`)
              - 2-element tuple indicating which port the probe was
                deployed on, eg. (19, 'W')

    .. 'port' -- 2-element tuple indicating which port the probe was
                deployed on. e.g. (19, 'W') => deployed on port 19 on
                the west side of the machine. Second elements
                descriptors should follow:
                  'T'  = top
                  'TW' = top-west
                  'W'  = west
                  'BW' = bottom-west
                  'B'  = bottom
                  'BE' = bottome-east
                  'E'  = east
                  'TE' = top-east
    """
    # Extracting Data:
    #  dset = h5py.get() returns a view of the dataset (dset)
    #  From here, instantiating from dset will create a copy of the
    #    data. If you want to keep views then one could use
    #    dset.values.view().  The dset.vlaues is the np.ndarray.
    #  To extract data, fancy indexing [::] can be used directly on
    #    dset or dset.values.

    def __new__(cls, hdf_file, board, channel,
                index=None, digitizer=None, adc=None,
                config_name=None, keep_bits=False, silent=False,
                **kwargs):
        """
        When inheriting from numpy, the object creation and
        initialization is handled by __new__ instead of __init__.

        :param hdf_file:
        :param int board:
        :param int channel:
        :param index: index/indices of shots to be extracted
        :type index: :code:`None`, int, list(int), or
            slice(start, stop, skip)
        :param str digitizer:
        :param str adc:
        :param str config_name:
        :param bool keep_bits: set :code:`True` keep data in bits opposed
            to converting to voltage

        .. note::

            Keyword :code:`shots` was renamed to :code:`index` in
            version 0.1.3.dev1.  Keyword :code:`shots` will still work,
            but will be deprecated in the future.
        """
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
        #
        # TODO: add error handling for .get() of dheader
        # TODO: add error handling for 'Offset' field in dheader
        # TODO: add digitizer key to self.info

        # initiate warning string
        warn_str = ''

        # Condition digitizer keyword
        if digitizer is None:
            warn_str = ('** Warning: Digitizer not specified so '
                        "assuming the 'main_digitizer' ({})".format(
                            hdf_file.file_map.main_digitizer.info[
                                'group name'])
                        + " defined in the mappings.")
            digi_map = hdf_file.file_map.main_digitizer
        else:
            if digitizer not in hdf_file.file_map.digitizers:
                raise KeyError('Specified Digitizer is not among known '
                               'digitizers')
            else:
                digi_map = hdf_file.file_map.digitizers[digitizer]

        # Note: digi_map.construct_dataset_name has conditioning for
        #       board, channel, adc, and config_name
        dname, d_info = digi_map.construct_dataset_name(
            board, channel, config_name=config_name, adc=adc,
            return_info=True, silent=silent)
        dpath = digi_map.info['group path'] + '/' + dname
        dset = hdf_file.get(dpath)
        dheader = hdf_file.get(dpath + ' headers')

        # backwards compatibility for 'shots' keyword which was changed
        # to index in v0.1.3.dev1
        # - keyword 'index' will always take precedence over 'shots'
        #   keyword
        #
        if 'shots' in kwargs and index is None:
            index = kwargs['shots']

        # Condition index keyword
        # Valid index types are: None, int, list(int), and slice()
        # - None      => extract all indices
        # - int       => extract shot with index int
        # - list(int) => extract shots with indices specified in list
        # - slice(start, stop, skip)
        #             => same as [start:stop:skip]
        #
        if index is None:
            if dset.shape[0] == 1:
                # data = dset[0, :]
                index = 0
            else:
                # data = dset[()]
                index = slice(None)
        elif isinstance(index, int):
            if index in range(dset.shape[0]) \
                    or -index-1 in range(dset.shape[0]):
                # data = dset[index, :]
                pass
            else:
                raise ValueError('index is not in range({})'.format(
                    dset.shape[0]))
        elif isinstance(index, list):
            # all elements need to be integers
            if all(isinstance(s, int) for s in index):
                # condition list
                index.sort()
                index = list(set(index))
                newindex = []
                for s in index:
                    if s < 0:
                        s = -s-1
                    if s in range(dset.shape[0]):
                        if s not in newindex:
                            newindex.append(s)
                    else:
                        warn_str += (
                            '\n** Warning: shot {} not a '.format(s)
                            + 'valid index, range({})'.format(
                                dset.shape[0]))
                newindex.sort()

                if len(newindex) != 0:
                    # data = dset[newindex, :]
                    index = newindex
                else:
                    raise ValueError('index: none of the elements are '
                                     'in range({})'.format(dset.shape[0]
                                                           ))
            else:
                raise ValueError("index keyword needs to be None, int, "
                                 "list(int), or slice object")
        elif isinstance(index, slice):
            # data = dset[index, :]
            pass
        else:
            raise ValueError("index keyword needs to be None, int, "
                             "list(int), or slice object")

        # Construct obj
        # - obj will be a numpy record array
        #
        # 1st column of the digi data header contains the shot number
        shotkey = dheader.dtype.names[0]
        sigtype = '<f4' if not keep_bits else dset.dtype
        mytype = [('shotnum', dheader[shotkey].dtype),
                  ('signal', sigtype, dset.shape[1])]
        shape = (dheader[shotkey][index].size,)
        data = np.empty(shape, dtype=mytype)
        data['shotnum'] = dheader[shotkey]
        data['signal'] = dset[index, :]
        obj = data.view(np.recarray)

        # data = dset[index, :]
        # obj = data.view(cls)
        # obj.header = dheader

        # assign dataset info
        obj.info = {
            'hdf file': hdf_file.filename.split('/')[-1],
            'dataset name': dname,
            'dataset path': dpath,
            'digitizer': d_info['digitizer'],
            'configuration name': d_info['configuration name'],
            'adc': d_info['adc'],
            'bit': d_info['bit'],
            'sample rate': d_info['sample rate'],
            'sample average': d_info['sample average (hardware)'],
            'shot average': d_info['shot average (software)'],
            'board': board,
            'channel': channel,
            'voltage offset': dheader['Offset'][0],
            'probe name': None,
            'port': (None, None)}

        # convert to voltage
        if not keep_bits:
            offset = abs(obj.info['voltage offset'])
            dv = 2.0 * offset / (2. ** obj.info['bit'] - 1.)
            obj['signal'] = obj['signal'].astype(np.float32, copy=False)
            obj['signal'] = (dv * obj['signal']) - offset

        return obj

    def __array_finalize__(self, obj):
        # according to numpy documentation:
        #  __array__finalize__(self, obj) is called whenever the system
        #  internally allocates a new array from obj, where obj is a
        #  subclass (subtype) of the (big)ndarray. It can be used to
        #  change attributes of self after construction (so as to ensure
        #  a 2-d matrix for example), or to update meta-information from
        #  the parent. Subclasses inherit a default implementation of
        #  this method that does nothing.

        # Define info attribute
        # - getattr() searches obj for the 'info' attribute. If the
        #   attribute exists, then it's returned. If the attribute does
        #   NOT exist, then the 3rd arg is returned as a default value.
        self.info = getattr(obj, 'info',
                            {'hdf file': None,
                             'dataset name': None,
                             'dataset path': None,
                             'configuration name': None,
                             'adc': None,
                             'bit': None,
                             'sample rate': (None, 'MHz'),
                             'sample average': None,
                             'shot average': None,
                             'board': None,
                             'channel': None,
                             'voltage offset': None,
                             'probe name': None,
                             'port': (None, None)})

    def __init__(self, *args, **kwargs):
        super().__init__()

        # convert to voltage
        # if not keep_bits:
        #    offset = abs(self.info['voltage offset'])
        #    dv = 2.0 * offset / (2. ** obj.info['bit'] - 1.)
        #    self = (dv * self) - offset

    def convert_to_v(self):
        """
        :return: Convert DAQ signal from bits to voltage.

        .. Warning:: Not implemented yet
        """
        raise NotImplementedError

    def convert_to_t(self):
        """
        :return: Convert DAQ signal dependent axis from index to time.

        .. Warning:: Not implemented yet
        """
        raise NotImplementedError

    @property
    def dt(self):
        """
        :return: time-step dt (in sec) from the 'sample rate' dict()
            item of :py:data:`self.info`.
        """
        # define unit conversions
        units = {'GHz': 1.E9, 'MHz': 1.E6, 'kHz': 1.E3, 'Hz': 1.0}

        # calc base dt
        dt = 1.0 / (self.info['sample rate'][0] *
                    units[self.info['sample rate'][1]])

        # adjust for hardware averaging
        if self.info['sample average'] is not None:
            print('sample ave')
            dt = dt * float(self.info['sample average'])
        else:
            print('no sample average')

        return dt

    @property
    def dv(self):
        """
        :return: voltage-step dv (in Volts) from the 'bit' and 'voltage
            offset' dict() items of :py:data:`self.info`.
        """
        dv = (2.0 * abs(self.info['voltage offset']) /
              (2. ** self.info['bit'] - 1.))
        return dv

    def full_path(self):
        """
        :return: full path of the dataset in the HDF5 file.

        .. Warning:: Not implemented yet
        """
        raise NotImplementedError
