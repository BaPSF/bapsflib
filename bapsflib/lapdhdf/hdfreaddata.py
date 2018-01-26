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
#

import numpy as np
import time

from .hdfreadcontrol import hdfReadControl, condition_controls
from bapsflib.plasma import core


class hdfReadData(np.recarray):
    """
    Reads the data out of the HDF5 file:
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
                intersection_set=True, silent=False,
                robust_define=False, **kwargs):
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

        # initialize timing
        if 'timeit' in kwargs:
            timeit = kwargs['timeit']
            if timeit:
                tt = [time.time()]
            else:
                timeit = False
        else:
            timeit = False

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

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - hdf_file conditioning: '
                  '{} ms'.format((tt[-1]-tt[-2])*1.E3))

        # ---- Check for Control Device Addition ---
        # condition controls
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

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - add_controls conditioning: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # ---- Gather Digi Dataset Info ----
        #
        # Note: digi_map.construct_dataset_name has conditioning for
        #       board, channel, adc, and
        #
        # dname      - digitizer dataset name
        # dpath      - full path to digitizer dataset
        # dset       - digitizer h5py.Dataset object (data is still on
        #              disk)
        # dheader    - header dataset for the digitizer dataset, this
        #              has the shot number values
        # shotnumkey - field name for shot number column in the digi
        #              header dataset (dheader)
        #
        dname, d_info = digi_map.construct_dataset_name(
            board, channel, config_name=config_name, adc=adc,
            return_info=True, silent=silent)
        dpath = digi_map.info['group path'] + '/' + dname
        dset = hdf_file.get(dpath)
        dheader = hdf_file.get(dpath + ' headers')
        shotnumkey = dheader.dtype.names[0]

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - get dset and dheader: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # ---- Condition shots, index, and shotnum ----
        # shots   -- same as index (legacy, do NOT use)
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
        # Through conditioning the following are defined (whether index
        # or shotnum is given):
        # index   -- row index of digitizer dataset (dset)
        #            ~ will be an int array of valid indices or a bool
        #              array indicating valid indices
        # shotnum -- int array of global HDF5 shot numbers to be added
        #            to data
        #            ~ data['shotnum'] = shotnum
        # sni     -- int or bool array for indexing shotnum (and
        #            consequently data['shotnum']
        #            ~ provides a one-to-one mapping to index
        #            ~ data['shotnum'][sni] = dset[index, shotnumkey]
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
        # Note: I'm letting the slicing of dset[index, shotnumkey] to
        #       throw the appropriate errors
        if shotnum is not None:
            # ignore index keyword if shotnum is used
            index = None
        elif index is None:
            index = 0 if dset.shape[0] == 1 else slice(None, None, None)

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - condition index: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # Condition shotnum keyword
        # - If shotnum is a slice object then catch it and convert it to
        #   a list
        if type(shotnum) is slice:
            # determine largest possible shot number
            last_sn = dheader[-1, shotnumkey]
            if shotnum.stop is not None:
                stop_sn = max(shotnum.stop, last_sn+1)
            else:
                stop_sn = last_sn + 1

            # get the start, stop, and step for the shot number array
            start, stop, step = shotnum.indices(stop_sn)

            # determine smallest possible shot number
            # - intersection_set = True
            #   * start = max of first_sn and shotnum.start
            # - intersection_set = False
            #   * start = min of first_sn and shotnum.start
            first_sn = [dheader[0, shotnumkey]]
            if shotnum.start is not None:
                # ensure shot numbers are >= 1
                if start <= 0:
                    start = 1

                # add to first_sn
                first_sn.append(start)
            start = max(first_sn) if intersection_set else min(first_sn)

            # re-define shotnum as a list
            shotnum = np.arange(start, stop, step).tolist()

        # Ensure 'shotnum' is valid
        # - here 'shotnum' will be converted from its keyword type to a
        #   1D array containing the list of shot numbers to be included
        #   in the returned obj array
        #
        if index is not None:
            # - index conditioning should ensure index is not None only
            #   if shotnum is not specified (i.e. shotnum is None and
            #   index is not None)
            #
            # shotnum = dset_sn[index].view()
            shotnum = dheader[index, shotnumkey].view()
            if type(shotnum) is not np.ndarray:
                shotnum = np.array([shotnum]).view()

            # define sni
            sni = np.ones(shotnum.shape[0], dtype=bool)

            # ensure obj will not be zero
            if shotnum.shape[0] == 0:
                raise ValueError(
                    'Input arguments would result in a null array')

            # convert index to np.ndarray
            if type(index) is int:
                index = np.array([index])
            elif type(index) is list:
                index = np.array(index)
            elif type(index) is slice:
                start, stop, step = index.indices(dheader.shape[0])
                index = np.arange(start, stop, step)
        elif type(shotnum) is int:
            # ensure shotnum is valid and determine its corresponding
            # index
            #
            index, shotnum, sni = condition_shotnum_int(shotnum,
                                                        dheader,
                                                        shotnumkey)
        elif type(shotnum) is list:
            # shotnum's have to be ints and >=1
            if all(type(s) is int for s in shotnum):
                index, shotnum, sni = \
                    condition_shotnum_list(shotnum, dheader, shotnumkey,
                                           intersection_set)
            else:
                raise ValueError('Valid shotnum not passed')
        else:
            raise ValueError('Valid shotnum not passed')

        # squeeze shotnum
        if len(shotnum.shape) != 1:
            shotnum = shotnum.squeeze()

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - condition shotnum: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # ---- Retrieve Control Data ---
        # 1. retrieve the numpy array for control data
        # 2. re-filter shotnum if intersection_set=True s.t. only
        #    shotnum's w/ control data are returned
        #
        # grab control device dataset
        #
        # - this will ensure cdata.shape == data.shape all the time
        # - shotnum should always be a ndarray at this point
        #
        if controls is not None:
            cdata = hdfReadControl(hdf_file, controls,
                                   assume_controls_conditioned=True,
                                   shotnum=shotnum.tolist(),
                                   intersection_set=intersection_set,
                                   silent=silent)

            # print execution timing
            if timeit:
                tt.append(time.time())
                print('tt - read in cdata (control data): '
                      '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

            # re-filter index, shotnum, and sni
            # - only need to be filtered if intersection_set=True
            # - for intersection_set=True, shotnum and index are
            #   one-to-one
            if intersection_set:
                new_sn_mask = np.isin(shotnum, cdata['shotnum'])
                shotnum = shotnum[new_sn_mask]
                index = index[new_sn_mask]
                sni = np.ones(shotnum.shape[0], dtype=bool)

        else:
            cdata = None

        # ---- Construct obj ---
        # - obj will be a numpy record array
        #
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
            for subdtype in cdata.dtype.descr:
                if subdtype[0] not in [d[0] for d in dtype]:
                    dtype.append(subdtype)

        # Define numpy array
        data = np.empty(shape, dtype=dtype)

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - define data: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # fill 'shotnum' field of data array
        data['shotnum'] = shotnum

        # make sure index is not an ndarray
        if type(index) is np.ndarray:
            index = index.tolist()

        # double check shot numbers
        if robust_define:
            # Double check that the correct shot numbers are being read
            # in
            #
            # NOTE: for some odd reason an HDF5 compound can not be
            #       indexed with a numpy array, whereas, a HDF5 scalar
            #       dataset can be
            #
            sn_double = dheader[index, shotnumkey].view()
            if type(sn_double) is not np.ndarray:
                sn_double = np.array([sn_double])
            if not np.array_equal(shotnum[sni], sn_double):
                raise AssertionError(
                    'routine is not indexing shot numbers properly')
            else:
                print('!! Shot number indexing working properly.')

        # fill remaining fields of data array
        if intersection_set:
            # fill signal
            data['signal'] = dset[index, ...].view()

            # fill controls
            if controls is not None:
                # find intersection shot number indices
                csni = np.in1d(cdata['shotnum'], shotnum)

                # fill xyz
                if 'xyz' in cdata.dtype.names:
                    data['xyz'] = cdata['xyz'][csni, ...]
                else:
                    data['xyz'] = np.nan

                # fill remaining controls
                for field in cdata.dtype.names:
                    if field not in ['shotnum', 'xyz']:
                        data[field] = cdata[field][csni, ...]
            else:
                # fill xyz
                data['xyz'] = np.nan
        else:
            # non-intersection fill
            #
            # fill signal
            data['signal'][sni] = dset[index, ...].view()
            null_fiiler = -99999 if data['signal'].dtype <= np.int \
                else np.nan
            data['signal'][np.logical_not(sni)] = null_fiiler

            # fill controls
            if controls is not None:
                # NOTE: if intersection_set=False, then cdata was
                #       generated with the same settings and
                #       data['shotnum'] and cdata['shotnum'] should be
                #       identical
                #
                if not np.array_equal(data['shotnum'],
                                      cdata['shotnum']):
                    raise ValueError(
                        "data['shotnum'] and cdata['shotnum'] are not"
                        " equal")

                # fill xyz
                if 'xyz' in cdata.dtype.names:
                    data['xyz'] = cdata['xyz']
                else:
                    data['xyz'] = np.nan

                # fill remaining controls
                for field in cdata.dtype.names:
                    if field not in ['shotnum', 'xyz']:
                        data[field] = cdata[field]
            else:
                # fill xyz
                data['xyz'] = np.nan

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - fill data array: '
                  '{} ms'.format((tt[-1] - tt[-2]) * 1.E3))

        # Define obj to be returned
        obj = data.view(cls)
        #
        # obj = data.view(np.recarray)
        #
        # Note: if np.recarray is used instead of cls then the
        #       returned object will be of class np.recarray instead
        #       of hdfReadData.  In that case, __init__ is never called
        #       and the hdfReadData methods are never bound.

        # get voltage offset
        try:
            voffset = dheader[0, 'Offset']
        except ValueError:
            voffset = None
            keep_bits = True
            warn_str += '\nCould not find voltage offset, forcing ' \
                        'keep_bits=True'

        # assign dataset meta-info
        obj._info = {
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
            'voltage offset': voffset,
            'probe name': None,
            'port': (None, None)
        }

        # plasma parameter dict
        obj._plasma = {
            'Bo': None,
            'kT': None,
            'kTe': None,
            'kTi': None,
            'gamma': core.FloatUnit(1.0, 'arb'),
            'm_e': core.ME,
            'm_i': None,
            'n': None,
            'n_e': None,
            'n_i': None,
            'Z': None
        }

        # convert to voltage
        if not keep_bits:
            offset = abs(obj.info['voltage offset'])
            # dv = 2.0 * offset / (2. ** obj._info['bit'] - 1.)
            obj['signal'] = obj['signal'].astype(np.float32, copy=False)
            obj['signal'] = (obj.dv * obj['signal']) - offset

        # print warnings
        if not silent and warn_str != '':
            print(warn_str)

        # print execution timing
        if timeit:
            tt.append(time.time())
            print('tt - execution time: '
                  '{} ms'.format((tt[-1] - tt[0]) * 1.E3))
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

        # Define _info attribute
        # - getattr() searches obj for the '_info' attribute. If the
        #   attribute exists, then it's returned. If the attribute does
        #   NOT exist, then the 3rd arg is returned as a default value.
        self._info = getattr(obj, '_info', {
            'hdf file': None,
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
            'port': (None, None)
        })

        # Define plasma attribute
        self._plasma = getattr(obj, '_plasma', {
            'Bo': None,
            'kT': None,
            'kTe': None,
            'kTi': None,
            'gamma': core.FloatUnit(1.0, 'arb'),
            'm_e': core.ME,
            'm_i': None,
            'n': None,
            'n_e': None,
            'n_i': None,
            'Z': None
        })

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
    def info(self):
        """
        A dictionary of metadata for the extracted data. The
        dict() keys are:

        .. list-table::
            :widths: 5 3 11

            * - :const:`hdf file`
              - `str`
              - HDF5 file name the data was retrieved from
            * - :const:`dataset name`
              - `str`
              - name of the dataset
            * - :const:`dataset path`
              - `str`
              - path to said dataset in the HDF5 file
            * - :const:`digitizer`
              - `str`
              - digitizer group name
            * - :const:`configuration name`
              - `str`
              - name of data configuration
            * - :const:`adc`
              - `str`
              - analog-digital converter in which the data was recorded
                on
            * - :const:`bit`
              - `int`
              - bit resolution for the adc
            * - :const:`sample rate`
              - (`int`, `float`)
              - tuple containing sample rate, e.g. (100.0, 'MHz')
            * - :const:`sample rate`
              - `int`
              - (hardware sampling) number of data sample average
                together
            * - :const:`shot average`
              - `int`
              - (software averaging) number of shot sequences averaged
                together
            * - :const:`board`
              - `int`
              - board that the probe was connected to
            * - :const:`channel`
              - `int`
              - channel of the board that the probe was connected to
            * - :const:`voltage offset`
              - `float`
              - voltage offset of the digitized signal
            * - :const:`probe name`
              - `str`
              - name of deployed probe...empty for user to use at
                his/her discretion
            * - :const:`port`
              - (`int`, `str`)
              - 2-element tuple indicating which port the probe was
                deployed on, eg. (19, 'W')

        .. 'port' -- 2-element tuple indicating which port the probe was
                     deployed on. e.g. (19, 'W') => deployed on port 19
                     on the west side of the machine. Second elements
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
        return self._info

    @property
    def dt(self):
        """
        :return: time-step size (in sec) calculated from the
            'sample rate' item in :attr:`info`.
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
            and 'voltage offset' items in :attr:`info`.
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

    @property
    def plasma(self):
        """
        Dictionary of plasma parameters. (All quantities are in cgs
        units except temperature is in eV)

        +----------------+---------------------------------------------+
        | Base Values                                                  |
        +================+=============================================+
        | :const:`Bo`    | magnetic field                              |
        +----------------+---------------------------------------------+
        | :const:`kT`    | temperature (generic)                       |
        +----------------+---------------------------------------------+
        | :const:`kTe`   | electron temperature                        |
        +----------------+---------------------------------------------+
        | :const:`kTi`   | ion temperature                             |
        +----------------+---------------------------------------------+
        | :const:`gamma` | adiabatic index                             |
        +----------------+---------------------------------------------+
        | :const:`m_e`   | electron mass                               |
        +----------------+---------------------------------------------+
        | :const:`m_i`   | ion mass                                    |
        +----------------+---------------------------------------------+
        | :const:`n`     | plasma number density                       |
        +----------------+---------------------------------------------+
        | :const:`n_e`   | electron number density                     |
        +----------------+---------------------------------------------+
        | :const:`n_i`   | ion number density                          |
        +----------------+---------------------------------------------+
        | :const:`Z`     | ion charge number                           |
        +----------------+---------------------------------------------+
        | Calculated Values                                            |
        +----------------+---------------------------------------------+
        | :const:`fce`   | electron cyclotron frequency                |
        +----------------+---------------------------------------------+
        | :const:`fci`   | ion cyclotron frequency                     |
        +----------------+---------------------------------------------+
        | :const:`fpe`   | electron plasma frequency                   |
        +----------------+---------------------------------------------+
        | :const:`fpi`   | ion plasma frequency                        |
        +----------------+---------------------------------------------+
        | :const:`fUH`   | Upper-Hybrid Resonance frequency            |
        +----------------+---------------------------------------------+
        | :const:`lD`    | Debye Length                                |
        +----------------+---------------------------------------------+
        | :const:`lpe`   | electron-inertial length                    |
        +----------------+---------------------------------------------+
        | :const:`lpi`   | ion-inertial length                         |
        +----------------+---------------------------------------------+
        | :const:`rce`   | electron gyroradius                         |
        +----------------+---------------------------------------------+
        | :const:`rci`   | ion gyroradius                              |
        +----------------+---------------------------------------------+
        | :const:`cs`    | ion sound speed                             |
        +----------------+---------------------------------------------+
        | :const:`VA`    | Alfven speed                                |
        +----------------+---------------------------------------------+
        | :const:`vTe`   | electron thermal velocity                   |
        +----------------+---------------------------------------------+
        | :const:`vTi`   | ion thermal velocity                        |
        +----------------+---------------------------------------------+
        """
        return self._plasma

    def set_plasma(self, Bo, kTe, kTi, m_i, n_e, Z, gamma=None,
                   **kwargs):
        """
        Set :attr:`plasma` and add key frequency, length, and velocity
        parameters. (all quantities in cgs except temperature is in eV)

        :param float Bo: magnetic field (in Gauss)
        :param float kTe: electron temperature (in eV)
        :param float kTi: ion temperature (in eV)
        :param float m_i: ion mass (in g)
        :param float n_e: electron number density (in cm^-3)
        :param int Z: ion charge number
        :param float gamma: adiabatic index (arb.)
        """
        # define base values
        self._plasma['Bo'] = core.FloatUnit(Bo, 'G')
        self._plasma['kTe'] = core.FloatUnit(kTe, 'eV')
        self._plasma['kTi'] = core.FloatUnit(kTi, 'eV')
        self._plasma['m_i'] = core.FloatUnit(m_i, 'g')
        self._plasma['n_e'] = core.FloatUnit(n_e, 'cm^-3')
        self._plasma['Z'] = core.IntUnit(Z, 'arb')

        # define ion number density
        self._plasma['n_i'] = core.FloatUnit(
            self._plasma['n_e'] / self._plasma['Z'], 'cm^-3')

        # define gamma (adiabatic index)
        # - default = 1.0
        if gamma is not None:
            self._plasma['gamma'] = core.FloatUnit(gamma, 'arb')

        # define plasma temperature
        # - if omitted then assumed kTe
        # TODO: double check assumption
        if 'kT' in kwargs:
            self._plasma['kT'] = core.FloatUnit(kwargs['kT'], 'eV')
        else:
            self._plasma['kT'] = core.FloatUnit(kTe, 'eV')

        # define plasma number density
        # - if omitted then assumed n_e
        if 'n' in kwargs:
            self._plasma['n'] = core.FloatUnit(kwargs['n'], 'cm^-3')
        else:
            self._plasma['n'] = core.FloatUnit(n_e, 'cm^-3')

        # add key plasma constants
        self._update_plasma_constants()

    def set_plamsa_value(self, key, value):
        """
        Re-define one of the base plasma values (Bo, gamma, kT, kTe,
        kTi, m_i, n, n_e, or Z) in the :attr:`plasma` dictionary.

        :param str key: one of the base plasma values
        :param value: value for key
        """
        # set plasma value
        if key == 'Bo':
            self._plasma['Bo'] = core.FloatUnit(value, 'G')
        elif key == 'gamma':
            self._plasma['gamma'] = core.FloatUnit(value, 'arb')
        elif key in ['kT', 'kTe', 'kTi']:
            self._plasma[key] = core.FloatUnit(value, 'eV')

            if key == 'kTe' and self._plasma['kt'] is None:
                self._plasma['kT'] = self._plasma[key]
        elif key == 'm_i':
            self._plasma[key] = core.FloatUnit(value, 'g')
        elif key in ['n', 'n_e']:
            self._plasma[key] = core.FloatUnit(value, 'cm^-3')

            # re-calc n_i and n
            if key == 'n_e':
                self._plasma['n_i'] = core.FloatUnit(
                    self._plasma['n_e'] / self._plasma['Z'], 'cm^-3')

                if self._plasma['n'] is None:
                    self._plasma['n'] = self._plasma['n_e']
        elif key == 'Z':
            self._plasma[key] = core.IntUnit(value, 'arb')

            # re-calc n_i
            self._plasma['n_i'] = \
                core.FloatUnit(self._plasma['n_e'] / self._plasma['Z'],
                               'cm^-3')

        # update key plasma constants
        self._update_plasma_constants()

    def _update_plasma_constants(self):
        """
        Updates the calculated plasma constants (fci, fce, fpe, etc.) in
        :attr:`plasma`.
        """
        # add key frequencies
        self._plasma['fce'] = core.fce(**self._plasma)
        self._plasma['fci'] = core.fci(**self._plasma)
        self._plasma['fpe'] = core.fpe(**self._plasma)
        self._plasma['fpi'] = core.fpi(**self._plasma)
        self._plasma['fUH'] = core.fUH(**self._plasma)
        self._plasma['fLH'] = core.fLH(**self._plasma)

        # add key lengths
        self._plasma['lD'] = core.lD(**self._plasma)
        self._plasma['lpe'] = core.lpe(**self._plasma)
        self._plasma['lpi'] = core.lpi(**self._plasma)
        self._plasma['rce'] = core.rce(**self._plasma)
        self._plasma['rci'] = core.rci(**self._plasma)

        # add key velocities
        self._plasma['cs'] = core.cs(**self._plasma)
        self._plasma['VA'] = core.VA(**self._plasma)
        self._plasma['vTe'] = core.vTe(**self._plasma)
        self._plasma['vTi'] = core.vTi(**self._plasma)


def condition_shotnum_int(shotnum, dheader, shotnumkey):
    # Variable  - Returned as
    # index     - int
    # shotnum   - np.array([int], dtype=uint32)
    # sni       - np.array([bool], dtype=bool)
    #
    if dheader.shape[0] == 1:
        # only one possible index and shotnum
        if shotnum == dheader[0, shotnumkey]:
            index = 0
        else:
            raise ValueError(
                'shotnum [{}] would result in a'.format(shotnum)
                + ' null array')
    elif shotnum >= 1:
        # get 1st and last shot number for further conditioning
        first_sn, last_sn = dheader[[-1, 0], shotnumkey]

        if last_sn - first_sn + 1 == dheader.shape[0]:
            # shot numbers are sequential
            if shotnum <= last_sn:
                index = shotnum - first_sn
            else:
                # shotnum not in dataset
                raise ValueError(
                    'shotnum [{}] would result'.format(shotnum)
                    + ' in a null array')
        elif first_sn <= shotnum <= last_sn:
            # shot numbers are NOT sequential, but shotnum may
            # be in the array
            step_from_front = shotnum - first_sn
            step_from_end = last_sn - shotnum

            if dheader.shape[0] <= \
                    min(step_from_front, step_from_end) + 1:
                # dheader.shape is smaller than the theoretical
                # sequential array
                dset_sn = dheader[shotnumkey].view()
                index_arr = np.where(dset_sn == shotnum)[0]

                if index_arr.shape[0] == 1:
                    index = index_arr[0]
                elif index_arr.shape[0] == 0:
                    # shotnum not found
                    raise ValueError(
                        'shotnum [{}] would result in'.format(shotnum)
                        + ' a null array')
                else:
                    raise ValueError(
                        'something went wrong...to many shotnum'
                        ' indices found')
            elif step_from_front <= step_from_end:
                # extracting from the beginning of the array
                # is the smallest
                some_dset_sn = dheader[0:step_from_front + 1,
                                       shotnumkey]
                index_arr = np.where(some_dset_sn == shotnum)[0]

                if index_arr.shape[0] == 1:
                    index = index_arr[0]
                elif index_arr.shape[0] == 0:
                    # shotnum not found
                    raise ValueError(
                        'shotnum [{}] would result in'.format(shotnum)
                        + ' a null array')
                else:
                    raise ValueError(
                        'something went wrong...to many shotnum'
                        ' indices found')
            else:
                # extracting from the end of the array is the
                # smallest
                start, stop, step = \
                    slice(-step_from_end - 1,
                          None,
                          None).indices(dheader.shape[0])
                some_dset_sn = dheader[start::, shotnumkey]
                index_arr = np.where(some_dset_sn == shotnum)[0]

                if index_arr.shape[0] == 1:
                    index = index_arr[0] + start
                elif index_arr.shape[0] == 0:
                    # shotnum not found
                    raise ValueError(
                        'shotnum [{}] would result in'.format(shotnum)
                        + ' a null array')
                else:
                    raise ValueError(
                        'something went wrong...to many shotnum'
                        ' indices found')
        else:
            raise ValueError(
                'shotnum [{}] would result in a'.format(shotnum)
                + ' null array')
    else:
        raise ValueError(
            'shotnum [{}] would result in a'.format(shotnum)
            + ' null array')

    # define sni
    # - if shotnum is an int then index, shotnum, and sni
    #   are all one-to-one
    sni = np.array([True], dtype=bool)

    # make shotnum a np.array
    shotnum = np.array([shotnum])

    # make index a np.array
    if type(index) is not np.ndarray:
        if type(index) is list:
            index = np.array(index, dtype=np.uint32)
        else:
            index = np.array([index])

    # return calculated arrays
    return index.view(), shotnum.view(), sni.view()


def condition_shotnum_list(shotnum, dheader, shotnumkey,
                           intersection_set):
    # Variable  - Returned as
    # index     - int or list(int)
    # shotnum   - np.array([int], dtype=uint32)
    # sni       - np.array([bool], dtype=bool)
    #
    # remove shot numbers less-than or equal to 0
    shotnum.sort()
    shotnum = list(set(shotnum))
    shotnum.sort()
    if min(shotnum) <= 0:
        # remove values less-than or equal to 0
        new_sn = [sn for sn in shotnum if sn > 0]
        shotnum = new_sn

    # remove shot numbers greater-than largest shot number
    # in dataset
    if intersection_set:
        last_sn = dheader[-1, shotnumkey]
        if max(shotnum) > last_sn:
            new_sn = [sn for sn in shotnum if sn <= last_sn]
            shotnum = new_sn

    # ensure shotnum is not empty
    if len(shotnum) == 0:
        raise ValueError('Valid shotnum not passed.')

    # convert shotnum to np.array
    # - shotnum is always a list up to this point
    shotnum = np.array(shotnum).view()

    # get corresponding indices for shotnum
    # build associated sni array
    #
    if dheader.shape[0] == 1:
        # only on possible index for shotnum
        only_sn = dheader[0, shotnumkey]
        if only_sn in shotnum:
            index = 0

            if intersection_set:
                shotnum = only_sn
                sni = np.array([True], dtype=bool)
            else:
                sni = np.where(shotnum == only_sn, True, False)
        else:
            raise ValueError(
                'shotnum(s) [{}] would'.format(shotnum)
                + ' result in a null array')
    else:
        # get 1st and last shot number for further
        # conditioning
        first_sn, last_sn = dheader[[-1, 0], shotnumkey]

        if last_sn - first_sn + 1 == dheader.shape[0]:
            # shot numbers are sequential
            index = shotnum - first_sn

            # build sni
            # - this will also mask index s.t. index has
            #   no values outside dheader.shape
            sni = index < dheader.shape[0]
            index = index[sni]
        else:
            # shot numbers are NOT sequential
            # TODO: check for more efficient read in methods
            #
            step_front_read = shotnum[-1] - first_sn
            step_end_read = last_sn - shotnum[0]

            if dheader.shape[0] <= 1 + min(step_front_read,
                                           step_end_read):
                # dheader.shape is smaller than the
                # theoretical sequential reads from either
                # end of the array
                dset_sn = dheader[shotnumkey].view()
                sni = np.isin(shotnum, dset_sn)

                # intersect shot numbers
                if intersection_set and not np.all(sni):
                    shotnum = shotnum[sni]
                    sni = np.isin(shotnum, dset_sn)

                # define index
                index = np.where(np.isin(dset_sn, shotnum))[0]
            elif step_front_read <= step_end_read:
                # extracting from the beginning of the array
                # is the smallest
                some_dset_sn = dheader[0:step_front_read + 1,
                                       shotnumkey]
                sni = np.isin(shotnum, some_dset_sn)

                # intersect shot numbers
                if intersection_set and not np.all(sni):
                    shotnum = shotnum[sni]
                    sni = np.isin(shotnum, some_dset_sn)

                # define index
                index = np.where(np.isin(some_dset_sn, shotnum))[0]
            else:
                # extracting from the end of the array is
                # the smallest
                start, stop, step = \
                    slice(-step_end_read - 1,
                          None,
                          None).indices(dheader.shape[0])
                some_dset_sn = dheader[start::, shotnumkey]
                sni = np.isin(shotnum, some_dset_sn)

                # intersect shot numbers
                if intersection_set and not np.all(sni):
                    shotnum = shotnum[sni]
                    sni = np.isin(shotnum, some_dset_sn)

                # define index
                index = np.where(np.isin(some_dset_sn, shotnum))[0]
                if index.shape[0] != 0:
                    index += start

    # ensure obj will not be zero
    if shotnum.shape[0] == 0:
        raise ValueError(
            'Input shotnum would result in a null array')

    # return calculated arrays
    return index.view(), shotnum.view(), sni.view()
