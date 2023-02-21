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
"""
Module containing the main `~bapsflib._hdf.utils.hdfreaddata.HDFReadData` class.
"""
__all__ = ["HDFReadData"]

import astropy.units as u
import copy
import numpy as np
import os
import time

from typing import Union
from warnings import warn

from bapsflib._hdf.utils.file import File
from bapsflib._hdf.utils.hdfreadcontrols import HDFReadControls
from bapsflib._hdf.utils.helpers import (
    build_sndr_for_simple_dset,
    condition_controls,
    condition_shotnum,
    do_shotnum_intersection,
)
from bapsflib.plasma import core


# noinspection PyInitNewSignature
class HDFReadData(np.ndarray):
    """
    Reads digitizer and control device data from the HDF5 file. Control
    device data is extracted using
    :class:`~.hdfreadcontrols.HDFReadControls` and combined with the
    digitizer data.

    This class constructs and returns a structured numpy array.  The
    data in the array is grouped into three categories:

    #. shot numbers which are contained in the :code:`'shotnum'` field
    #. digitizer data which is contained in the :code:`'signal'` field
    #. control device data which is represented by the remaining fields
       in the numpy array.  These field names are polymorphic and are
       defined by the control device mapping class. (see
       :class:`~.hdfreadcontrols.HDFReadControls` for more detail)

    Data that is not shot number specific is stored in the :attr:`info`
    attribute.

    .. note::

        * Every returned numpy array will have the :code:`'xyz'` field,
          which is reserved for probe position data.  If a control
          device specifies this field, then field will be filled with
          the control device data;otherwise, the field will be filled
          with :code:`numpy.nan` values.
    """

    __example_doc__ = """
    :Example: Here data is extracted from the digitizer 
        :code:`'SIS crate'` and position data is mated from the
        control device :code:`'6K Compumotor'`.
        
        >>> # open HDF5 file
        >>> f = bapsflib.lapd.File('test.hdf5')
        >>>
        >>> # read digitizer data from board 1, channel 1,
        >>> # - this is equivalent to 
        >>> #   f.read_data(1, 1)
        >>> data = HDFReadData(f, 1, 1)
        >>> data.dtype
        dtype([('shotnum', '<u4'), ('signal', '<f4', (100,)), 
              ('xyz', '<f4', (3,))])
        >>>
        >>> # display shot numbers
        >>> data['shotnum']
        array([  1,  2, ..., 98, 99], dtype=uint32)
        >>>
        >>> # show 'signal' values for shot number 1
        >>> data['signal'][0]
        array([-0.41381955, -0.4134333 , -0.4118886 , ..., -0.41127062,
               -0.4105754 , -0.41119337], dtype=float32)
        >>>
        >>> # show 'xyz' values for shot number 1
        >>> data['xyz'][0]
        array([nan, nan, nan], dtype=float32)
        >>>
        >>> # read digitizer data while adding '6K Compumotor' data
        >>> # from receptacle (configuration) 3
        >>> data = HDFReadData(f, 1, 1, 
                               add_controls=[('6K Compumotor', 3)])
        >>> data.dtype
        dtype([('shotnum', '<u4'), ('signal', '<f4', (100,)), 
               ('xyz', '<f4', (3,)), ('ptip_rot_theta', '<f8'), 
               ('ptip_rot_phi', '<f8')])
        >>>
        >>> # show 'xyz' values for shot number 1
        >>> data['xyz'][0]
        array([ -32. ,   15. , 1022.4], dtype=float32)

    """

    def __new__(
        cls,
        hdf_file: File,
        board: int,
        channel: int,
        index=slice(None),
        shotnum=slice(None),
        digitizer=None,
        config_name=None,
        adc=None,
        keep_bits=False,
        add_controls=None,
        intersection_set=True,
        **kwargs,
    ):
        """
        :param hdf_file: HDF5 file object
        :param board: analog-digital-converter board number
        :param channel: analog-digital-converter channel number
        :param index: dataset row indices to be sliced (overridden
            by :code:`shotnum`)
        :type index: Union[int, List[int], slice, numpy.ndarray]
        :param shotnum: HDF5 file shot number(s) indicating data
            entries to be extracted (overrides :code:`index`)
        :type shotnum: Union[int, List[int], slice, numpy.ndarray]
        :param str digitizer: digitizer name
        :param str adc: name of analog-digital-converter
        :param str config_name: name of the digitizer configuration
        :param bool keep_bits: set :code:`True` to keep data in bits,
            :code:`False` (DEFAULT) to convert data to voltage
        :param add_controls: a list indicating the desired control
            device names and their configuration name (if more than one
            configuration exists)
        :type controls: Union[str, Iterable[str, Tuple[str, Any]]]
        :param bool intersection_set: :code:`True` (DEFAULT) will force
            the returned shot numbers to be the intersection of
            :data:`shotnum` and the shot numbers contained in each
            control device and digitizer dataset. :code:`False` will
            return the union of shot numbers.

        Behavior of :data:`index`, :data:`shotnum` and
        :data:`intersection_set`:

        .. note::

            * The :data:`shotnum` keyword will always override the
              :data:`index` keyword, but, due to extra overhead
              required for identifying shot number locations in the
              digitizer dataset, the :data:`index` keyword will always
              execute quicker than the :data:`shotnum` keyword.
        """
        # initialize timing
        tt = []
        if "timeit" in kwargs:  # pragma: no cover
            timeit = kwargs["timeit"]
            if timeit:
                tt.append(time.time())
            else:
                timeit = False
        else:
            timeit = False

        # ---- Condition hdf_file                                   ----
        # - `hdf_file` is a lapd.File object
        #
        if not isinstance(hdf_file, File):
            raise TypeError(
                f"`hdf_file` is NOT type `{File.__module__}.{File.__qualname__}`"
            )

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - `hdf_file` conditioning: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # ---- Examine file map object                              ----
        # grab instance of `HDFMap`
        _fmap = hdf_file.file_map

        # ---- Condition `add_controls`                             ----
        # Check for non-empty controls
        if bool(add_controls) and not bool(_fmap.controls):
            raise ValueError("There are no control devices in the HDF5 file.")

        # condition controls
        if bool(add_controls):
            controls = condition_controls(hdf_file, add_controls)
        else:
            controls = []

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - `add_controls` conditioning: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # ---- Condition `digitizer` keyword                        ----
        if not bool(_fmap.digitizers):
            raise ValueError("There are no digitizers in the HDF5 file.")
        elif digitizer is None:
            if not bool(_fmap.main_digitizer):
                raise ValueError(
                    "No main digitizer is identified..."
                    "need to specify `digitizer` kwarg"
                )

            why = (
                f"Digitizer not specified so assuming the 'main_digitizer' "
                f"({_fmap.main_digitizer.device_name}) defined in the mappings."
            )
            warn(why)
            _dmap = _fmap.main_digitizer
        else:
            try:
                _dmap = _fmap.digitizers[digitizer]
            except KeyError:
                raise ValueError(
                    f"Specified Digitizer '{digitizer}' is not among known "
                    f"digitizers ({list(_fmap.digitizers)})"
                )

        # ---- Gather Digi Dataset Info                             ----
        #
        # Note: _dmap.construct_dataset_name has conditioning for
        #       board, channel, adc, and
        #
        # dname      - digitizer dataset name
        # dhname     - digitizer header dataset name
        # dpath      - full path to digitizer group
        # dset       - digitizer h5py.Dataset object
        # dheader    - dset associated header dataset
        # shotnumkey - field name for shot number column in dheader
        #
        # Build kwargs for construct_dataset_name()
        kwargs = {"return_info": True}
        if config_name is not None:
            kwargs["config_name"] = config_name
        if adc is not None:
            kwargs["adc"] = adc

        # Get datasets
        dname, d_info = _dmap.construct_dataset_name(board, channel, **kwargs)
        dhname = _dmap.construct_header_dataset_name(board, channel, **kwargs)
        dpath = f"{_dmap.info['group path']}/"
        dset = hdf_file.get(dpath + dname)
        dheader = hdf_file.get(dpath + dhname)

        # define `config_name`
        if config_name is None:
            config_name = _dmap.active_configs[0]

        # define `shotnumkey`
        shotnumkey = _dmap.configs[config_name]["shotnum"]["dset field"][0]

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - get dset and dheader: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # ---- Condition shots, index, and shotnum ----
        # index   -- row index of digitizer dataset
        #            ~ indexed at 0
        #            ~ supersedes any other indexing keywords
        # shotnum -- global HDF5 file shot number
        #            ~ this is the index used to link values between
        #              datasets
        #            ~ overridden by `index`
        #
        # Through conditioning the following are (re-)defined
        # index   -- row index of digitizer dataset (dset)
        #            ~ numpy.ndarray
        #            ~ dtype = np.integer
        #            ~ shape = (num_of_indices,)
        #
        # shotnum -- global HDF5 shot numbers
        #            ~ index at 1
        #            ~ will be a filtered version of input kwarg shotnum
        #              based on intersection_set
        #            ~ numpy.ndarray
        #            ~ dtype = np.uint32
        #            ~ shape = (sn_size, )
        #
        # sni     -- bool array for providing a one-to-one mapping
        #            between shotnum and index
        #            ~ shotnum[sni] = dheader[index, shotnumkey]
        #            ~ data['signal'][sni, ...] = dset[index, ...]
        #            ~ data['singal'][np.logical_not(sni), ...] = np.nan
        #            ~ numpy.ndarray
        #            ~ dtype = np.bool
        #            ~ shape = (sn_size, )
        #            ~ np.count_nonzero(arr[0,...]) = num_of_indices
        #
        # - Indexing behavior: (depends on intersection_set)
        #
        #   ~ intersection_set = True (DEFAULT)
        #     * the returned array will only contain shot numbers that
        #       are in the intersection of shotnum, the digitizer
        #       dataset, and all the specified control device datasets
        #
        #   ~ intersection_set = False
        #     * the returned array will contain all shot numbers
        #       specified by shotnum (>= 1)
        #     * if a dataset does not included a shot number contained
        #       in shotnum, then its entry in the returned array will
        #       be given a NULL value depending on the dtype
        #
        # Determine if indexing w.r.t. `index` or `shotnum`
        index_with = "index"
        if isinstance(index, slice):
            if index == slice(None):
                if not isinstance(shotnum, slice):
                    index_with = "shotnum"
                elif shotnum != slice(None):
                    index_with = "shotnum"

        # Condition `index` and `shotnum` keywords
        # - Valid indexing types are: int, list(int), slice(), and
        #   np.ndarray
        #
        if index_with == "index":
            # Condition `index` keyword
            #
            # Note: I'm letting the slicing of dset[index, shotnumkey]
            #       throw the appropriate errors
            #
            # Define `shotnum`
            # - Note: h5py datasets can NOT be sliced using numpy arrays
            #
            # convert `index` to np.ndarray
            sn_size = dheader.size
            if isinstance(index, int):
                index = np.array([index], dtype=np.int32)
            elif isinstance(index, list):
                index = np.array(index, dtype=np.int32)
            elif isinstance(index, slice):
                start, stop, step = index.indices(sn_size)
                index = np.arange(start, stop, step, dtype=np.int32)
            elif isinstance(index, type(Ellipsis)):
                index = np.arange(0, sn_size, 1, dtype=np.int32)
            elif isinstance(index, np.ndarray):
                pass
            else:
                raise TypeError("Valid `index` type not passed.")

            # convert (VALID) negative indices to positive
            neg_index_mask = np.where((index < 0) & (index >= -sn_size), True, False)
            if np.any(neg_index_mask):
                adj_ii = index[neg_index_mask] % sn_size
                index[neg_index_mask] = adj_ii
            index = np.unique(index)

            # define `shotnum`
            shotnum = dheader[index.tolist(), shotnumkey]

            # define sni
            sni = np.ones(shotnum.shape[0], dtype=bool)

            # print execution timing
            if timeit:  # pragma: no cover
                tt.append(time.time())
                print(f"tt - condition index: {(tt[-1] - tt[-2]) * 1.0e3} ms")
        else:
            # Condition `shotnum` keyword
            #
            # convert `shotnum` to np.ndarray
            """
            if isinstance(shotnum, slice):
                # determine largest possible shot number
                last_sn = dheader[-1, shotnumkey]
                if shotnum.stop is not None:
                    stop_sn = max(shotnum.stop, last_sn + 1)
                else:
                    stop_sn = last_sn + 1

                # get the start, stop, and step for the shot number
                # array
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
                else:
                    # start wasn't specified in slice object
                    start = min(first_sn)

                # adjust start for intersection_set
                if intersection_set:
                    first_sn.append(start)
                    start = max(first_sn)

                # re-define shotnum as a list
                shotnum = np.arange(start, stop, step).tolist()
            elif isinstance(shotnum, int):
                shotnum = [shotnum]
            elif isinstance(shotnum, list):
                # ensure all elements are int
                if not all(isinstance(sn, int) for sn in shotnum):
                    raise ValueError('Valid `shotnum` not passed')
            else:
                raise ValueError('Valid `shotnum` not passed')
            """
            # perform `shotnum` conditioning
            # - `shotnum` is returned as a numpy array
            shotnum = condition_shotnum(shotnum, {"digi": dheader}, {"digi": shotnumkey})

            # Calc. the corresponding `index` and `sni`
            # - `shotnum` will be converted from list to np.array
            # - `index` and `sni` will be np.array's
            """
            index, shotnum, sni = \
                condition_shotnum(shotnum, dheader, shotnumkey,
                                  intersection_set)
            """
            index, sni = build_sndr_for_simple_dset(shotnum, dheader, shotnumkey)

            # perform intersection
            if intersection_set:
                shotnum, sni_dict, index_dict = do_shotnum_intersection(
                    shotnum, {"digi": sni}, {"digi": index}
                )
                sni = sni_dict["digi"]
                index = index_dict["digi"]

            # print execution timing
            if timeit:  # pragma: no cover
                tt.append(time.time())
                print(f"tt - condition shotnum: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # ---- Retrieve Control Data                                ----
        # 1. retrieve the numpy array for control data
        # 2. re-filter shotnum if intersection_set=True s.t. only
        #    shotnum's w/ control data are returned
        #
        # grab control device dataset
        #
        # - this will ensure cdata.shape == data.shape all the time
        # - shotnum should always be a ndarray at this point
        #
        if len(controls) != 0:
            cdata = HDFReadControls(
                hdf_file,
                controls,
                assume_controls_conditioned=True,
                shotnum=shotnum,
                intersection_set=intersection_set,
            )

            # print execution timing
            if timeit:  # pragma: no cover
                tt.append(time.time())
                print(
                    f"tt - read in cdata (control data): {(tt[-1] - tt[-2]) * 1.0e3} ms"
                )

            # re-filter index, shotnum, and sni
            # - only need to be filtered if intersection_set=True
            # - for intersection_set=True, shotnum and index are
            #   one-to-one
            #
            if intersection_set:
                new_sn_mask = np.isin(shotnum, cdata["shotnum"])
                shotnum = shotnum[new_sn_mask]
                index = index[new_sn_mask]
                sni = np.ones(shotnum.shape[0], dtype=bool)
        else:
            cdata = None

        # ---- Build `obj`                                          ----
        # Define dtype and shape
        # - 1st column of the digi data header contains the global HDF5
        #   file shot number
        # - shotkey = is the field name/key of the dheader shot number
        #   column
        sigtype = np.float32 if not keep_bits else dset.dtype
        shape = shotnum.shape
        dtype = [
            ("shotnum", np.uint32, 1),
            ("signal", sigtype, dset.shape[1]),
            ("xyz", np.float32, 3),
        ]
        if len(controls) != 0:
            for subdtype in cdata.dtype.descr:
                if subdtype[0] not in [d[0] for d in dtype]:
                    dtype.append(subdtype)

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - define dtype: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # Initialize data array
        data = np.empty(shape, dtype=dtype)

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - initialize data np.ndarray: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # fill 'shotnum' field of data array
        data["shotnum"] = shotnum

        # fill 'signal' fields of data array
        index = index.tolist()
        if intersection_set:
            # fill signal
            data["signal"] = dset[index, ...]
        else:
            # fill signal
            data["signal"][sni] = dset[index, ...]
            if np.issubdtype(data["signal"].dtype, np.integer):
                data["signal"][np.logical_not(sni)] = 0
            else:
                # dtype is np.floating
                data["signal"][np.logical_not(sni)] = np.nan

        # fill fields related to controls
        if len(controls) != 0:
            # Note: shot numbers of cdata and data are one-to-one
            #       by this point so intersection_set is irrelevant
            #
            if not np.array_equal(data["shotnum"], cdata["shotnum"]):  # pragma: no cover
                # this should never happen
                raise ValueError("data['shotnum'] and cdata['shotnum'] are not equal")

            # fill xyz
            if "xyz" in cdata.dtype.names:
                data["xyz"] = cdata["xyz"]
            else:
                data["xyz"] = np.nan

            # fill remaining controls
            for field in cdata.dtype.names:
                if field not in ("shotnum", "xyz"):
                    data[field] = cdata[field]
        else:
            # fill xyz
            data["xyz"] = np.nan

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - fill data array: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # Define obj to be returned
        obj = data.view(cls)

        # get voltage offset
        try:
            voffset = dheader[0, "Offset"] * u.volt
        except ValueError:
            warn("Digitizer header dataset is missing the voltage 'Offset' field. ")
            voffset = None

        # assign dataset meta-info
        obj._info = {
            "source file": os.path.abspath(hdf_file.filename),
            "device group path": _dmap.info["group path"],
            "device dataset path": dpath + dname,
            "digitizer": d_info["digitizer"],
            "configuration name": d_info["configuration name"],
            "adc": d_info["adc"],
            "bit": d_info["bit"],
            "clock rate": d_info["clock rate"],
            "sample average": d_info["sample average (hardware)"],
            "shot average": d_info["shot average (software)"],
            "board": board,
            "channel": channel,
            "voltage offset": voffset,
            "probe name": None,
            "port": (None, None),
            "signal units": u.bit,
        }
        if cdata is not None:
            obj._info["controls"] = copy.deepcopy(cdata.info["controls"])
        else:
            obj._info["controls"] = {}

        # plasma parameter dict
        obj._plasma = {
            "Bo": None,
            "kT": None,
            "kTe": None,
            "kTi": None,
            "gamma": core.FloatUnit(1.0, "arb"),
            "m_e": core.ME,
            "m_i": None,
            "n": None,
            "n_e": None,
            "n_i": None,
            "Z": None,
        }  # pragma: no cover

        # convert to voltage
        # - 'signal' dtype is assigned based on keep_bit
        #
        # obj['signal'] = obj['signal'].astype(np.float32, copy=False)
        #
        if not keep_bits:
            if obj.dv is None:
                warn("Unable to calculated voltage step size...'signal' remains as bits")
            else:
                # define offset
                offset = abs(obj.info["voltage offset"].value)

                # calc voltage
                obj["signal"] = (obj.dv.value * obj["signal"]) - offset

                # update 'signal units'
                obj._info["signal units"] = u.volt

        # print execution timing
        if timeit:  # pragma: no cover
            tt.append(time.time())
            print(f"tt - execution time: {(tt[-1] - tt[-2]) * 1.0e3} ms")

        # return obj
        return obj

    def __array_finalize__(self, obj):
        # This should only be True during explicit construction
        # if obj is None:
        if obj is None or obj.__class__ is np.ndarray:
            return

        # Define _info attribute
        self._info = getattr(
            obj,
            "_info",
            {
                "source file": None,
                "device group path": None,
                "device dataset path": None,
                "configuration name": None,
                "adc": None,
                "bit": None,
                "clock rate": None,
                "sample average": None,
                "shot average": None,
                "board": None,
                "channel": None,
                "voltage offset": None,
                "probe name": None,
                "port": (None, None),
                "signal units": None,
                "controls": {},
            },
        )

        # Define plasma attribute
        self._plasma = getattr(
            obj,
            "_plasma",
            {
                "Bo": None,
                "kT": None,
                "kTe": None,
                "kTi": None,
                "gamma": core.FloatUnit(1.0, "arb"),
                "m_e": core.ME,
                "m_i": None,
                "n": None,
                "n_e": None,
                "n_i": None,
                "Z": None,
            },
        )  # pragma: no cover

    def convert_signal(self, to_volt=False, to_bits=False, force=False):
        """converts signal from volts (bits) to bits (volts)"""
        #
        # 1. investigate if 'signal' values are np.integer or
        #    np.floating
        #    - np.integer => 'signal' is in bits
        #    - np.floating => 'signal' is in volts
        # 2. only convert if requested conversion is not current state
        # 3. update 'signal units' in self._info
        #
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
            * - :const:`clock rate`
              - (`int`, `float`)
              - tuple containing clock rate, e.g. (100.0, 'MHz')
            * - :const:`clock rate`
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
    def dt(self) -> Union[u.Quantity, None]:
        """
        Temporal step size (in sec) calculated from the
        :code:`'clock rate'` and :code:`'sample average'` items in
        :attr:`info`.  Returns :code:`None` if step size can not be
        calculated.
        """
        if not isinstance(self.info["clock rate"], u.Quantity):
            return

        # calc base dt
        dt = 1.0 / self.info["clock rate"]
        dt = dt.to("s")

        # adjust for hardware averaging
        if self.info["sample average"] is not None:
            dt = dt * float(self.info["sample average"])

        return dt

    @property
    def dv(self) -> Union[u.Quantity, None]:
        """
        Voltage step size (in volts) calculated from the :code:`'bit'`
        and :code:`'voltage offset'` items in :attr:`info`.  Returns
        :code:`None` if step size can not be calculated.
        """
        if self.info["voltage offset"] is None:
            return
        elif self.info["bit"] is None:
            return

        dv = 2.0 * abs(self.info["voltage offset"]) / (2.0 ** self.info["bit"] - 1.0)
        return dv

    @property
    def plasma(self):  # pragma: no cover
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

    def set_plasma(
        self, Bo, kTe, kTi, m_i, n_e, Z, gamma=None, **kwargs
    ):  # pragma: no cover
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
        self._plasma["Bo"] = core.FloatUnit(Bo, "G")
        self._plasma["kTe"] = core.FloatUnit(kTe, "eV")
        self._plasma["kTi"] = core.FloatUnit(kTi, "eV")
        self._plasma["m_i"] = core.FloatUnit(m_i, "g")
        self._plasma["n_e"] = core.FloatUnit(n_e, "cm^-3")
        self._plasma["Z"] = core.IntUnit(Z, "arb")

        # define ion number density
        self._plasma["n_i"] = core.FloatUnit(
            self._plasma["n_e"] / self._plasma["Z"], "cm^-3"
        )

        # define gamma (adiabatic index)
        # - default = 1.0
        if gamma is not None:
            self._plasma["gamma"] = core.FloatUnit(gamma, "arb")

        # define plasma temperature
        # - if omitted then assumed kTe
        # TODO: double check assumption
        if "kT" in kwargs:
            self._plasma["kT"] = core.FloatUnit(kwargs["kT"], "eV")
        else:
            self._plasma["kT"] = core.FloatUnit(kTe, "eV")

        # define plasma number density
        # - if omitted then assumed n_e
        if "n" in kwargs:
            self._plasma["n"] = core.FloatUnit(kwargs["n"], "cm^-3")
        else:
            self._plasma["n"] = core.FloatUnit(n_e, "cm^-3")

        # add key plasma constants
        self._update_plasma_constants()

    def set_plasma_value(self, key, value):  # pragma: no cover
        """
        Re-define one of the base plasma values (Bo, gamma, kT, kTe,
        kTi, m_i, n, n_e, or Z) in the :attr:`plasma` dictionary.

        :param str key: one of the base plasma values
        :param value: value for key
        """
        # set plasma value
        if key == "Bo":
            self._plasma["Bo"] = core.FloatUnit(value, "G")
        elif key == "gamma":
            self._plasma["gamma"] = core.FloatUnit(value, "arb")
        elif key in ["kT", "kTe", "kTi"]:
            self._plasma[key] = core.FloatUnit(value, "eV")

            if key == "kTe" and self._plasma["kt"] is None:
                self._plasma["kT"] = self._plasma[key]
        elif key == "m_i":
            self._plasma[key] = core.FloatUnit(value, "g")
        elif key in ["n", "n_e"]:
            self._plasma[key] = core.FloatUnit(value, "cm^-3")

            # re-calc n_i and n
            if key == "n_e":
                self._plasma["n_i"] = core.FloatUnit(
                    self._plasma["n_e"] / self._plasma["Z"], "cm^-3"
                )

                if self._plasma["n"] is None:
                    self._plasma["n"] = self._plasma["n_e"]
        elif key == "Z":
            self._plasma[key] = core.IntUnit(value, "arb")

            # re-calc n_i
            self._plasma["n_i"] = core.FloatUnit(
                self._plasma["n_e"] / self._plasma["Z"], "cm^-3"
            )

        # update key plasma constants
        self._update_plasma_constants()

    def _update_plasma_constants(self):  # pragma: no cover
        """
        Updates the calculated plasma constants (fci, fce, fpe, etc.) in
        :attr:`plasma`.
        """
        # add key frequencies
        self._plasma["fce"] = core.fce(**self._plasma)
        self._plasma["fci"] = core.fci(**self._plasma)
        self._plasma["fpe"] = core.fpe(**self._plasma)
        self._plasma["fpi"] = core.fpi(**self._plasma)
        self._plasma["fUH"] = core.fUH(**self._plasma)
        self._plasma["fLH"] = core.fLH(**self._plasma)

        # add key lengths
        self._plasma["lD"] = core.lD(**self._plasma)
        self._plasma["lpe"] = core.lpe(**self._plasma)
        self._plasma["lpi"] = core.lpi(**self._plasma)
        self._plasma["rce"] = core.rce(**self._plasma)
        self._plasma["rci"] = core.rci(**self._plasma)

        # add key velocities
        self._plasma["cs"] = core.cs(**self._plasma)
        self._plasma["VA"] = core.VA(**self._plasma)
        self._plasma["vTe"] = core.vTe(**self._plasma)
        self._plasma["vTi"] = core.vTi(**self._plasma)


# add example to __new__ docstring
HDFReadData.__new__.__doc__ += "\n"
for line in HDFReadData.__example_doc__.splitlines():
    HDFReadData.__new__.__doc__ += f"    {line}\n"


'''
def condition_shotnum(shotnum, dheader, shotnumkey,
                      intersection_set):
    """
    Conditions **shotnum** against the digitizer header dataset.

    :param shotnum: desired HDF5 shot number(s)
    :type shotnum: list(int)
    :param dheader: digitizer header dataset
    :param dheader: :class:`h5py.Dataset`
    :param str shotnumkey: field name in **dheader** that contains the
        shot numbers
    :param bool intersection_set: Set :code:`True` to intersect
        **shotnum** with the shot numbers in :code:`dheader[shotnumkey]`
    :return: index, shotnum, sni

    .. note::

        The returned :class:`numpy.ndarray`'s (:const:`index`,
        :const:`shotnum`, and :const:`sni`) follow the rule::

            shotnum[sni] = dheader[index, shotnumkey]
    """
    # Inputs:
    # shotnum           list(int)     - the desired shot number(s)
    # cheader           h5py.Dataset  - the digi header dataset
    # shotnumkey        str           - field name for the shot number
    #                                   column in dheader
    # intersection_set  bool          - intersect shotnum with
    #                                   dheader[shotnumkey]
    #
    # Returns:
    # index    np.array(dtype=uint32) - cdset row index for the
    #                                   specified shotnum
    # shotnum  np.array(dtype=uint32) - shot numbers
    # sni      np.array(dtype=bool)   - shotnum mask such that:
    #            shotnum[sni] = cdset[index, shotnumkey]
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

    # Calc. corresponding `index` and `sni` for shotnum
    # - intersection will after initial calculation
    #
    if dheader.shape[0] == 1:
        # only one possible shot number
        only_sn = dheader[0, shotnumkey]
        sni = np.where(shotnum == only_sn, True, False)
        index = np.array([0]) \
            if True in sni else np.empty(shape=0, dtype=np.uint32)
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
            sni = np.where(index < dheader.shape[0], True, False)
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

                # define index
                index = np.where(np.isin(dset_sn, shotnum))[0]
            elif step_front_read <= step_end_read:
                # extracting from the beginning of the array is the
                # smallest
                some_dset_sn = dheader[0:step_front_read + 1,
                                       shotnumkey]
                sni = np.isin(shotnum, some_dset_sn)

                # define index
                index = np.where(np.isin(some_dset_sn, shotnum))[0]
            else:
                # extracting from the end of the array is the smallest
                start, stop, step = \
                    slice(-step_end_read - 1,
                          None,
                          None).indices(dheader.shape[0])
                some_dset_sn = dheader[start::, shotnumkey]
                sni = np.isin(shotnum, some_dset_sn)

                # define index
                # NOTE: if index is empty (i.e. index.shape[0] == 0)
                #       then adding an int still returns an empty array
                index = np.where(np.isin(some_dset_sn, shotnum))[0]
                index += start
                
    # filter shotnum and ensure obj will not be empty
    if intersection_set:
        # check for empty shotnum
        if True not in sni:
            raise ValueError(
                'Input shotnum would result in a null array')

        # filter
        shotnum = shotnum[sni]
        sni = np.ones(shotnum.shape, dtype=bool)
    else:
        # empty shotnum
        if shotnum.shape[0] == 0:
            raise ValueError(
                'Input shotnum would result in a null array')

    # return calculated arrays
    return index.view(), shotnum.view(), sni.view()
'''
