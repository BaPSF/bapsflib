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
# TODO: decide on input args for reading out HDF5 data
#

import h5py
import numpy as np
import time

from .hdfreadcontrol import hdfReadControl, condition_controls,\
    gather_shotnums

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
                index=None, shotnum=None, digitizer=None, adc=None,
                config_name=None, keep_bits=False, add_controls=None,
                intersection_set=True, silent=False, **kwargs):
        """
        When inheriting from numpy, the object creation and
        initialization is handled by __new__ instead of __init__.

        :param hdf_file: object instance of the HDF5 file
        :type hdf_file: :class:`bapsflib.lapdhdf.files.File`
        :param int board: board number of data to be extracted
        :param int channel: channel number of data to be extracted
        :param index: row index/indices of dataset to be extracted
            (overridden by :code:`shotnum`)
        :type index: :code:`None`, int, list(int), or slice()
        :param shotnum: global HDF5 shot number (overrides
            :code:`index`)
        :type shotnum: :code:`None`, int, list(int), or slice()
        :param str digitizer: name of digitizer for which board and
            channel belong to
        :param str adc: name of analog-digital-converter in the
            digitizer for which board and channel belong to
        :param str config_name: name of the digitizer configuration to
            be used
        :param bool keep_bits: set :code:`True` to keep data in bits,
            :code:`False` (default) convert data to voltage
        :param add_controls: list of control devices whose data will
            be matched with the digitizer data
        :type add_controls: list of strings and/or 2-element tuples. If
            an element is a string, then the string is the control
            device name. If an element is a 2-element tuple, then
            tuple[0] is the control device name and tuple[1] is a unique
            specifier for that control device.
        :param bool intersection_set:
        :param bool silent: set :code:`True` to suppress command line
            print out of soft warnings

        .. note::

            Keyword :code:`shots` was renamed to :code:`index` in
            version 0.1.3.dev1.  Keyword :code:`shots` will still work,
            but will be deprecated in the future.
        """
        #
        # numpy uses __new__ to initialize objects, so an __init__ is
        # not necessary
        #
        # TODO: add error handling for .get() of dheader
        # TODO: add error handling for 'Offset' field in dheader

        # for timing
        tt = [time.time()]

        # initiate warning string
        warn_str = ''

        # ---- Condition hdf_file ----
        # Check hdf_file is a lapdhdf.File object
        try:
            file_map = hdf_file.file_map
        except AttributeError:
            raise AttributeError(
                'hdf_file needs to be of type lapdhdf.File')

        # Condition digitizer keyword
        if digitizer is None:
            warn_str = "** Warning: Digitizer not specified so " \
                + "assuming the 'main_digitizer' ({})".format(
                    file_map.main_digitizer.info[
                        'group name']) \
                + " defined in the mappings."
            digi_map = file_map.main_digitizer
        else:
            try:
                digi_map = hdf_file.file_map.digitizers[digitizer]
            except KeyError:
                raise KeyError('Specified Digitizer is not among known '
                               'digitizers')

        # ---- Check for Control Device Addition ---
        # condition controls
        tt.append(time.time())
        if add_controls is not None:
            controls = condition_controls(hdf_file, add_controls,
                                          silent=silent)

            # check controls is not empty
            if not controls:
                warn_str = '\n** Warning: no valid controls passed, ' \
                           'none added to array'
                controls = None
        else:
            controls = None
        tt.append(time.time())
        print('controls conditioning: {} ms'.format(
            (tt[-1]-tt[-2]) * 1.0e3))

        # ---- gather info about digi and control datasets ----
        #
        # get controls info
        # cset_sn - 1D array of either the intersection or union of shot
        #           numbers contained in the control device datasets
        #
        if controls is not None:
            method = 'intersection' if intersection_set else 'union'
            cset_sn = gather_shotnums(hdf_file, controls, method=method)

            # check resulting array won't be null
            if intersection_set and cset_sn.shape[0] == 0:
                raise ValueError(
                    'Input arguments would result in a null array')
        else:
            cset_sn = None
        tt.append(time.time())
        print('controls get shotnums: {} ms'.format(
            (tt[-1] - tt[-2]) * 1.0e3))

        # Digi Dataset Info
        # Note: digi_map.construct_dataset_name has conditioning for
        #       board, channel, adc, and
        #
        # dname   - digitizer dataset name
        # dpath   - full path to digitizer dataset
        # dset    - digitizer h5py.Dataset object (data is still on
        #           disk)
        # dset_sn - array of dataset shot numbers
        # dheader - header dataset for the digitizer dataset, this has
        #           the shot number values
        #
        dname, d_info = digi_map.construct_dataset_name(
            board, channel, config_name=config_name, adc=adc,
            return_info=True, silent=silent)
        dpath = digi_map.info['group path'] + '/' + dname
        dset = hdf_file.get(dpath)
        dheader = hdf_file.get(dpath + ' headers')
        shotnumkey = dheader.dtype.names[0]
        dset_sn = dheader[shotnumkey].view()
        tt.append(time.time())
        print('get dataset and info: {} ms'.format(
            (tt[-1] - tt[-2]) * 1.0e3))

        # ---- Condition shots, index, and shotnum ----
        # shots   -- same as index
        #            ~ overridden by index and shotnum
        #            ~ this is kept for backwards compatibility
        #            ~ 'shots' was renamed to 'index' in v0.1.3dev1
        # index   -- row index of digitizer dataset
        #            ~ indexed at 0
        #            ~ overridden by shotnum
        # shotnum -- global HDF5 file shot number
        #            ~ this is the index used to link values between
        #              datasets
        #            ~ supersedes any other indexing keyword
        #
        # - Indexing behavior: (depends on intersection_set)
        #
        #   ~ intersection_set is only considered if add_controls
        #     is not None
        #
        #   ~ intersection_set = True (DEFAULT)
        #     * will ensure the returned array will only contain shot
        #       numbers (shotnum) that has data in the digitizer dataset
        #       and all specified control device datasets
        #     * index
        #       > will be the row index of the digitizer dataset
        #       > may be trimmed to enforce shot number intersection of
        #         all datasets
        #     * shotnum
        #       > will be the desired global shot numbers
        #       > may be trimmed to enforce shot number intersection of
        #         all datasets
        #
        #   ~ intersection_set = False
        #     * does not enforce shot number intersection of all
        #       datasets. Instread, if a dataset does not include a
        #       specified shot number, then that entry will be given a
        #       numpy.nan value
        #     * index
        #       > will be the row index of the digitizer dataset
        #     * shotnum
        #       > will be the desired global shot numbers
        #
        # rename 'shots' to 'index'
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
        if shotnum is not None:
            # ignore index keyword if shotnum is used
            index = None
        elif index is None:
            index = 0 if dset.shape[0] == 1 else slice(None)
            # if dset.shape[0] == 1:
            #     # data = dset[0, :]
            #     index = 0
            # else:
            #     # data = dset[()]
            #     index = slice(None)
        elif type(index) is int:
            if not (index in range(dset.shape[0])
                    or -index - 1 in range(dset.shape[0])):
                raise ValueError('index is not in range({})'.format(
                    dset.shape[0]))
        elif type(index) is list:
            # all elements need to be integers
            if all(type(s) is int for s in index):
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
                    index = newindex
                else:
                    raise ValueError(
                        'index: none of the elements are in '
                        'range({})'.format(dset.shape[0]))
            else:
                raise ValueError("index keyword needs to be None, int, "
                                 "list(int), or slice object")
        elif type(index) is slice:
            # valid type
            pass
        else:
            raise ValueError("index keyword needs to be None, int, "
                             "list(int), or slice object")
        tt.append(time.time())
        print('condition index: {} ms'.format(
            (tt[-1] - tt[-2]) * 1.0e3))

        # Ensure 'shotnum' is valid
        # - here 'shotnum' will be converted frm its keyword type to a
        #   1D array containing the list of shot numbers to be included
        #   in the returned obj array
        #
        if index is not None:
            # - index conditioning should ensure index is not None only
            #   if shotnum is not specified (i.e. shotnum is None and
            #   index is not None)
            #
            shotnum = dset_sn[index].view()
            if type(shotnum) is np.int32:
                shotnum = np.array([shotnum]).view()

            # build intersection
            if intersection_set and cset_sn is not None:
                shotnum = np.intersect1d(shotnum, cset_sn).view()

            # ensure obj will not be zero
            if shotnum.shape[0] == 0:
                raise ValueError('Valid shotnum not passed')
        elif type(shotnum) is int:
            if shotnum in dset_sn:
                shotnum = np.array([shotnum])
            else:
                raise ValueError(
                    'shotnum [{}] is not a valid'.format(shotnum)
                    + ' shot number')
        elif type(shotnum) is list:
            # shotnum's have to be ints and >=1
            if all(type(s) is int for s in shotnum):
                # remove shot numbers less-than or equal to 0
                shotnum.sort()
                shotnum = list(set(shotnum))
                try:
                    zindex = shotnum.index(0)
                    del shotnum[:zindex+1]
                except ValueError:
                    # no values less-than or equal to 0
                    pass

                # convert shotnum to np.array
                if intersection_set and cset_sn is not None:
                    shotnum = np.intersect1d(shotnum, cset_sn).view()
                else:
                    shotnum = np.array(shotnum).view()

                # ensure obj will not be zero
                if shotnum.shape[0] == 0:
                    raise ValueError('Valid shotnum not passed')
            else:
                raise ValueError('Valid shotnum not passed')
        elif type(shotnum) is slice:
            try:
                if shotnum.start <= 0 or shotnum.stop <= 0:
                    raise ValueError('Valid shotnum not passed')
            except TypeError:
                if shotnum.stop is None:
                    raise ValueError('Valid shotnum not passed')
                elif shotnum.start is None:
                    shotnum = slice(shotnum.stop-1, shotnum.stop,
                                    shotnum.step)

            # convert shotnum to np.array
            if intersection_set and cset_sn is not None:
                shotnum = np.intersect1d(
                    np.arange(shotnum.start,
                              shotnum.stop,
                              shotnum.step),
                    cset_sn.view())
            else:
                shotnum = np.arange(shotnum.start, shotnum.stop,
                                    shotnum.step)

            # ensure obj will not be a zero dim array
            if shotnum.shape[0] == 0:
                raise ValueError('Valid shotnum not passed')
        else:
            raise ValueError('Valid shotnum not passed')
        tt.append(time.time())
        print('condition shotnum: {} ms'.format(
            (tt[-1] - tt[-2]) * 1.0e3))

        # ---- Construct obj ---
        # - obj will be a numpy record array
        #
        # grab control device dataset
        #
        if controls is not None:
            cset = hdfReadControl(hdf_file, controls,
                                  shotnum=np.ndarray.tolist(shotnum),
                                  intersection_set=intersection_set,
                                  silent=silent)
        tt.append(time.time())
        print('get cset: {} ms'.format(
            (tt[-1] - tt[-2]) * 1.0e3))

        # Define dtype for obj
        # - 1st column of the digi data header contains the global HDF5
        #   file shot number
        # - shotkey = is the field name/key of the dheader shot number
        #   column
        sigtype = '<f4' if not keep_bits else dset.dtype
        shape = shotnum.shape[0]
        dtype = [('shotnum', '<u4'),
                 ('signal', sigtype, dset.shape[1]),
                 ('xyz', '<f4', 3)]
        if controls is not None:
            for subdtype in cset.dtype.descr:
                if subdtype[0] not in [d[0] for d in dtype]:
                    dtype.append(subdtype)
        tt.append(time.time())
        print('define dtype: {} ms'.format(
              (tt[-1] - tt[-2]) * 1.0e3))

        # Define numpy array
        data = np.empty(shape, dtype=dtype)
        tt.append(time.time())
        print('initialized data array: {} ms'.format(
            (tt[-1] - tt[-2]) * 1.0e3))

        # fill array
        data['shotnum'] = shotnum
        if intersection_set:
            # fill signal
            sni = np.in1d(dheader[shotnumkey].view(), shotnum)
            data['signal'] = dset[sni, ...]

            # fill controls
            if controls is not None:
                # find intersection shot number indices
                sni = np.in1d(cset['shotnum'], shotnum)

                # fill xyz
                if 'xyz' in cset.dtype.names:
                    data['xyz'] = cset['xyz'][sni, ...]
                else:
                    data['xyz'] = np.nan

                # fill remaining controls
                for field in cset.dtype.names:
                    if field not in ['shotnum', 'xyz']:
                        data[field] = cset[field][sni, ...]
            else:
                # fill xyz
                data['xyz'] = np.nan
        else:
            # fill signal
            sn_intersect = np.intersect1d(shotnum,
                                          dheader[shotnumkey].view())
            dseti = np.in1d(dheader[shotnumkey].view(), sn_intersect)
            datai = np.in1d(data['shotnum'], sn_intersect)
            data['signal'][datai] = dset[dseti, ...].view()
            if data['signal'].dtype <= np.int:
                data['signal'][np.invert(datai)] = -99999
            else:
                data['signal'][np.invert(datai)] = np.nan

            # fill controls
            if controls is not None:
                # find intersection shot number indices
                sn_intersect = np.intersect1d(shotnum, cset['shotnum'])
                cseti = np.in1d(cset['shotnum'], sn_intersect)
                datai = np.in1d(data['shotnum'], sn_intersect)

                # fill xyz
                if 'xyz' in cset.dtype.names:
                    data['xyz'][datai, ...] = cset['xyz'][cseti, ...]
                    data['xyz'][np.invert(datai), ...] = np.nan
                else:
                    data['xyz'] = np.nan

                # fill remaining controls
                for field in cset.dtype.names:
                    if field not in ['shotnum', 'xyz']:
                        data[field][datai, ...] = \
                            cset[field][cseti, ...]
                        data[field][np.invert(datai), ...] = np.nan
            else:
                # fill xyz
                data['xyz'] = np.nan
        tt.append(time.time())
        print('Fill data array: {} ms'.format(
              (tt[-1] - tt[-2]) * 1.0e3))

        # Define obj to be returned
        obj = data.view(cls)
        #
        # obj = data.view(np.recarray)
        #
        # Note: if np.recarray is used instead of cls then the
        #       returned object will be of class np.recarray instead
        #       of hdfReadData.  In that case, __init__ is never called
        #       and the hdfReadData methods are never bound.
        tt.append(time.time())
        print('Define obj: {} ms'.format(
              (tt[-1] - tt[-2]) * 1.0e3))

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
        tt.append(time.time())
        print('Define obj.info: {} ms'.format(
              (tt[-1] - tt[-2]) * 1.0e3))

        # convert to voltage
        if not keep_bits:
            offset = abs(obj.info['voltage offset'])
            # dv = 2.0 * offset / (2. ** obj.info['bit'] - 1.)
            obj['signal'] = obj['signal'].astype(np.float32, copy=False)
            obj['signal'] = (obj.dv * obj['signal']) - offset
        tt.append(time.time())
        print('Convert signal to voltage: {} ms'.format(
              (tt[-1] - tt[-2]) * 1.0e3))

        # print warnings
        if not silent:
            print(warn_str)

        print('Exec time: {} ms'.format(
            (tt[-1] - tt[0]) * 1.0e3))
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
        if obj is None:
            return

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
        # Note: __init__ will only run if __new__ returns an object
        #       with class hdfReadData.  NumPy structure does allow for
        #       the return of objects with differing classes, see NumPy
        #       subclassing documentation.
        #
        super().__init__()

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
        :return: time-step size (in sec) calculated from the
            'sample rate' item in :attr:`self.info`.
        :rtype: float
        """
        # define unit conversions
        units = {'GHz': 1.E9, 'MHz': 1.E6, 'kHz': 1.E3, 'Hz': 1.0}

        # calc base dt
        dt = 1.0 / (self.info['sample rate'][0] *
                    units[self.info['sample rate'][1]])

        # adjust for hardware averaging
        if self.info['sample average'] is not None:
            dt = dt * float(self.info['sample average'])
        else:
            print('no sample average')

        return dt

    @property
    def dv(self):
        """
        :return: voltage-step size (in volts) calculated from the 'bit'
            and 'voltage offset' items in :attr:`self.info`.
        :rtype: float
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
