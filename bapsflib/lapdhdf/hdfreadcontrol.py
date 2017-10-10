# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#

import h5py
import numpy as np


class hdfReadControl(np.recarray):
    """
    Reads out data from a control device in the HDF5 file:
    """

    # Extracting Data:
    #  dset = h5py.get() returns a view of the dataset (dset)
    #  From here, instantiating from dset will create a copy of the
    #    data. If you want to keep views then one could use
    #    dset.values.view().  The dset.vlaues is the np.ndarray.
    #  To extract data, fancy indexing [::] can be used directly on
    #    dset or dset.values.

    def __new__(cls, hdf_file, controls,
                index=None, silent=False, **kwargs):
        """
        When inheriting from numpy, the object creation and
        initialization is handled by __new__ instead of __init__.

        :param hdf_file:
        :param controls:
        :param index: index/indices of shots to be extracted
        :type index: :code:`None`, int, list(int), or
            slice(start, stop, skip)
        :param str digitizer:
        :param str adc:
        :param str config_name:
        :param bool keep_bits: set :code:`True` keep data in bits
            opposed to converting to voltage

        .. note::

            Keyword :code:`shots` was renamed to :code:`index` in
            version 0.1.3.dev1.  Keyword :code:`shots` will still work,
            but will be deprecated in the future.
        """
        # param control:
        # - control is a string list naming the control to be read out
        # - if a control contains multiple devices, then it's entry in
        #   the control list must be a 2-element tuple where the 1st
        #   element is the control name and the 2nd element is a unique
        #   specifier.
        #   e.g. the '6K Compumotor' can have multiple probe drives
        #   which are identified by their receptacle number, so
        #
        #       controls = [('6K Compumotor', 1),]
        #
        #   would indicate a readout of receptacle 1 of the
        #   '6K Compumotor'
        # - The list can only contain one entry from each contype. i.e.
        #   This is valid:
        #
        #       control = ['6K Compumotor', 'Waveform', 'N5700_PS']
        #
        #   but this is not:
        #
        #       controls = ['6K Compumotor', 'NI_XZ']
        #
        # Order of Operations:
        #   1. check for file mapping attribute (hdf_obj.file_map)
        #   2. check for non-empty controls mapping
        #      (hdf_obj.file_map.controls)
        #   3. look for 'controls' in file_map.controls
        #   4. condition index keyword
        #   5. build recarray
        #   6. build obj.info (metadata)

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
                    or -index - 1 in range(dset.shape[0]):
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
                        s = -s - 1
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
        # - 1st column of the digi data header contains the global HDF5
        #   file shot number
        # - shotkey = is the field name/key of the dheader shot number
        #   column
        shotkey = dheader.dtype.names[0]
        sigtype = '<f4' if not keep_bits else dset.dtype
        mytype = [('shotnum', dheader[shotkey].dtype),
                  ('signal', sigtype, dset.shape[1]),
                  ('xyz', '<f4', 3)]
        shape = (dheader[shotkey][index].size,)
        data = np.empty(shape, dtype=mytype)
        data['shotnum'] = dheader[shotkey]
        data['signal'] = dset[index, :]
        data['xyz'].fill(np.nan)
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
        if obj is None: return

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

    def full_path(self):
        """
        :return: full path of the dataset in the HDF5 file.

        .. Warning:: Not implemented yet
        """
        raise NotImplementedError
