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
"""Module containing the main HDF5 `~bapsflib._hdf.utils.file.File` class."""

from __future__ import annotations

__all__ = ["File"]

import astropy.units as u
import h5py
import numpy as np
import os
import warnings

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from bapsflib._hdf.maps import HDFMapControls, HDFMapDigitizers, HDFMapMSI, HDFMapper
from bapsflib.utils.warnings import BaPSFWarning, HDFMappingWarning

if TYPE_CHECKING:  # pragma: no cover
    # This is done for typing purposes only.
    # An actual import would cause cyclical imports.
    from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate
    from bapsflib._hdf.utils.hdfoverview import HDFOverview
    from bapsflib._hdf.utils.hdfreadcontrols import HDFReadControls
    from bapsflib._hdf.utils.hdfreaddata import HDFReadData
    from bapsflib._hdf.utils.hdfreadmsi import HDFReadMSI


class File(h5py.File):
    """
    Open a HDF5 file created at the Basic Plasma Science Facility.

    All functionality of `h5py.File` is preserved (for details
    see http://docs.h5py.org/en/latest/)
    """

    def __init__(
        self,
        name: str,
        mode="r",
        control_path="/",
        digitizer_path="/",
        msi_path="/",
        silent=False,
        **kwargs,
    ):
        """
        Parameters
        ----------
        name : `str`
            name (and path) of file on disk

        mode : `str`, optional
            readonly ``'r'`` (DEFAULT) and read/write ``'r+'``

        control_path : `str`, optional
            internal HDF5 path to group containing control devices

        digitizer_path : `str`, optional
            internal HDF5 path to group containing digitizer devices
        msi_path : `str`, optional
            internal HDF5 path to group containing MSI devices

        silent : `bool`, optional
            set `True` to suppress warnings (`False` DEFAULT)
        kwargs : `dict`, optional
            additional keywords passed on to `h5py.File`

        Examples
        --------

            >>> # open HDF5 file
            >>> f = File('sample.hdf5',
            ...          control_path='Raw data + config',
            ...          digitizer_path='Raw data + config',
            ...          msi_path='MSI')
            >>> type(f)
            bapsflib._hdf.utils.file.File
        """
        # initialize
        if mode not in ("r", "r+"):
            raise ValueError(
                "Only `mode` readonly 'r' and read/write 'r+' are supported."
            )
        kwargs["mode"] = mode
        h5py.File.__init__(self, name, **kwargs)

        # -- define device paths --
        #: Internal HDF5 path for control devices. (DEFAULT ``'/'``)
        self.CONTROL_PATH = control_path

        #: Internal HDF5 path for digitizer devices.
        #: (DEFAULT ``'/'``)
        self.DIGITIZER_PATH = digitizer_path

        #: Internal HDF5 path for MSI devices. (DEFAULT ``'/'``)
        self.MSI_PATH = msi_path

        # -- map and build info --
        warn_filter = "ignore" if silent else "default"
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter, category=BaPSFWarning)

            # create map
            self._map_file()

            # build `_info` attribute
            self._build_info()

    def _build_info(self):
        """Builds the general :attr:`info` dictionary for the file."""
        # define file keys
        self._info = {
            "file": os.path.basename(self.filename),
            "absolute file path": os.path.abspath(self.filename),
        }

    def _map_file(self):
        """Map/re-map the HDF5 file. (Builds :attr:`file_map`)"""
        self._file_map = HDFMapper(
            self,
            control_path=self.CONTROL_PATH,
            digitizer_path=self.DIGITIZER_PATH,
            msi_path=self.MSI_PATH,
        )

    @property
    def controls(self) -> HDFMapControls:
        """Dictionary of control device mappings."""
        return self.file_map.controls

    @property
    def digitizers(self) -> HDFMapDigitizers:
        """Dictionary of digitizer device mappings"""
        return self.file_map.digitizers

    @property
    def file_map(self) -> HDFMapper:
        """HDF5 file map (`~bapsflib._hdf.maps.mapper.HDFMapper`)"""
        return self._file_map

    @property
    def info(self) -> Dict[str, Any]:
        """
        Dictionary of general info on the HDF5 file and the experimental
        run.
        """
        return self._info

    @property
    def msi(self) -> HDFMapMSI:
        """Dictionary of MSI device mappings."""
        return self.file_map.msi

    @property
    def overview(self) -> HDFOverview:
        """
        HDF5 file overview. (`~.hdfoverview.HDFOverview`)
        """
        # to avoid cyclical imports
        from bapsflib._hdf.utils.hdfoverview import HDFOverview

        return HDFOverview(self)

    def get_digitizer_specs(
        self,
        board: int,
        channel: int,
        *,
        digitizer: Optional[str] = None,
        adc: Optional[str] = None,
        config_name: Optional[str] = None,
        silent: bool = False,
    ) -> Dict[str, Any]:
        """
        Get a dictionary of the digitizer setup for the given ``board``
        and ``channel``.

        Parameters
        ----------
        board : `int`
            Digitizer board number.

        channel : `int`
            Digitizer channel number.

        digitizer : `str`, optional
            Digitizer name.  If `None`, then the digitizer will be
            inferred if only one digitizer was used. (DEFAULT: `None`)
        adc : `str`, optional
            Digitizer analog-digital-converter name.  If `None`, then
            the ``adc`` will be taken from the digitizer configuration
            assuming only one adc was used.  (DEFAULT: `None`)

        config_name : `str`, optional
            Digitizer configuration name.  If `None`, then the
            ``config_name`` will be taken from the digitizer
            configuration assuming only one active configuration was
            used. (DEFAULT: `None`)

        silent : `bool`
            Set `True` to suppress warnings. (DEFAULT: `False`)

        Returns
        -------
        Dict[str, Any]
            Dictionary of the digitizer setup for the specified
            ``board`` and ``channel``.

        Notes
        -----

        The returned dictionary will contain the following data:

        +---------------------------------+----------------------------------------+
        | Key                             | Description                            |
        +=================================+========================================+
        | ``"board"``                     | Digitizer board number.                |
        +---------------------------------+----------------------------------------+
        | ``"channel"``                   | Digitizer channel number.              |
        +---------------------------------+----------------------------------------+
        | ``"digitizer"``                 | Digitizer name.                        |
        +---------------------------------+----------------------------------------+
        | ``"adc"``                       | Name of analog-digital-converter.      |
        +---------------------------------+----------------------------------------+
        | ``"configuration name"``        | Name of digitizer configuration.       |
        +---------------------------------+----------------------------------------+
        | ``"nshotnum"``                  | Num. of shot numbers in the data run.  |
        +---------------------------------+----------------------------------------+
        | ``"nt"``                        | Num. of time samples.                  |
        +---------------------------------+----------------------------------------+
        | ``"bit"``                       | Bit-ness of the digitizer.             |
        +---------------------------------+----------------------------------------+
        | ``"clock rate"``                | Digitizer clock rate                   |
        +---------------------------------+----------------------------------------+
        | ``"shot average"``              | Num. of timeseries averaged together   |
        +---------------------------------+----------------------------------------+
        | ``"sample average"``            | Num. of time samples averaged together |
        +---------------------------------+----------------------------------------+
        | ``"device group path"``         | internal path to device group          |
        +---------------------------------+----------------------------------------+
        | ``"device dataset path"``       | internal path to digitizer dataset     |
        +---------------------------------+----------------------------------------+
        | ``"source file"``               | absolute path to HDF5 file             |
        +---------------------------------+----------------------------------------+
        | ``"time_dset_path"``            | internal path to time series dataset   |
        +---------------------------------+----------------------------------------+

        """
        if digitizer is None and len(self.digitizers) != 1:
            raise ValueError(
                f"The HDF5 file has {len(self.digitizers)} digitizers and can "
                f"not infer the desired digitizer.  Argument 'digitizer' "
                f"must specify one of {self.digitizers.keys()}."
            )
        elif digitizer is None:
            digitizer = list(self.digitizers.keys())[0]
            digi_map = self.digitizers[digitizer]
        elif not isinstance(digitizer, str):
            raise TypeError(
                "Argument 'digitizer' must be a string specifying one of "
                f"{list(self.digitizers.keys())}.  Got type {type(digitizer)}."
            )
        elif digitizer not in self.digitizers:
            raise ValueError(
                f"Argument 'digitizer' ({digitizer}) not in list of mapped "
                f"digitizers {list(self.digitizers.keys())}."
            )
        else:
            digi_map = self.digitizers[digitizer]  # type: HDFMapDigiTemplate

        with warnings.catch_warnings():
            _filter = "ignore" if silent else "default"
            warnings.simplefilter(_filter, category=HDFMappingWarning)
            name, _info = digi_map.construct_dataset_name(
                board,
                channel,
                adc=adc,
                config_name=config_name,
                return_info=True,
            )  # type: Dict[str, Any]

        _info["board"] = board
        _info["channel"] = channel
        _info["shot average"] = _info.pop("shot average (software)", None)
        _info["sample average"] = _info.pop("sample average (hardware)", None)
        _info["device group path"] = digi_map.group_path
        _info["device dataset path"] = f"{digi_map.group_path}/{name}"
        _info["source file"] = os.path.abspath(self.filename)

        time_dset = _info.pop("time_dset_path", None)
        if time_dset is not None:
            time_dset = f"{digi_map.group_path}/{time_dset}"
        _info["time_dset_path"] = time_dset

        return _info

    def get_time_array(self, data_info: HDFReadData | Dict[str, Any]) -> np.ndarray:
        """
        Get the time `numpy` array associated with the ``data_info``
        argument.

        ``data_info`` can be an
        `~bapsflib._hdf.utils.hdfreaddata.HDFReadData` object obtained
        using :meth:`read_data` or and information `dict` generated using
        :meth:`get_digitizer_specs`.

        Parameters
        ----------
        data_info : HDFReadData | Dict[str, Any]
            An `~bapsflib._hdf.utils.hdfreaddata.HDFReadData` object
            instance or a dictionary containing the necessary time
            meta-data.

        Returns
        -------
        np.ndarray
            A 1D `numpy` array containing the time series data.

        Notes
        -----

        The method uses the meta-data contained in either the
        information dictionary generated by :meth:`get_digitizer_specs`
        or the `~bapsflib._hdf.utils.hdfreaddata.HDFReadData.info`
        dictionary bound to
        `~bapsflib._hdf.utils.hdfreaddata.HDFReadData` (which is
        generated by method :meth:`read_data`).

        If the information dictionary contains the key ``"clock rate"``,
        then the time array will be calculated using the ``"clock rate"``,
        ``"nt"``, and ``"sample average"``.

        If ``"clock rate"`` is `None`, then the it is assumed the time
        series is stored in a dedicated dataset which is indicated by
        the ``"time_dset_path"`` key.

        Examples
        --------

        Retrieving the time series array AFTER reading out the digitizer
        data::

        >>> f = File("sample.hdf5")
        >>> data = f.read_data(0, 1, silent=True)
        >>> time_arr = f.get_time_array(data)

        Retrieving the time series array BEFORE reading out the digitizer
        data::

        >>> f = File("sample.hdf5")
        >>> _info = f.get_digitizer_specs(0, 1, silent=True)
        >>> time_arr = f.get_time_array(_info)

        """
        # to avoid cyclical imports
        from bapsflib._hdf.utils.hdfreaddata import HDFReadData

        if isinstance(data_info, HDFReadData):
            _info = data_info.info.copy()

            if "nt" not in _info:
                _info["nt"] = data_info["signal"].shape[1]
        elif not isinstance(data_info, dict):
            raise TypeError(
                "Argument 'data_info' must be a HDFReadData or dict object.  "
                "Pass in either data retrieved from `read_data()` or the "
                "information dictionary generated by `get_digitizer_specs()`."
            )
        else:
            _info = data_info

        if "clock rate" not in _info and "time_dset_path" not in _info:
            raise ValueError(
                "The `data_info` argument does NOT contain information about "
                "the digitizer clock rate or a dedicated time series dataset.  "
                "Pass in either data retrieved from `read_data()` or the "
                "information dictionary generated by `get_digitizer_specs()`."
            )

        # calculate time array based on clock rate and sample size (nt)
        clock_rate = _info.get("clock rate", None)
        if isinstance(clock_rate, u.Quantity):
            if "sample average" in _info:
                sample_average = _info["sample average"]
            elif "sample average (hardware)" in _info:
                sample_average = _info["sample average (hardware)"]
            else:
                sample_average = None
            sample_average = 1.0 if sample_average is None else float(sample_average)

            dt = (1 / clock_rate).to("s").value * sample_average
            nt = _info["nt"]

            time = np.arange(0, nt, 1, dtype=np.float32) * dt
            return time

        # look for a dedicate time array in the HDF5 file
        time_dset_path = _info.get("time_dset_path", None)
        if time_dset_path is None:
            raise ValueError(
                "Something went wrong.  The given data_info does NOT specify "
                "a dedicated time dataset in the HDF5 file nor does it "
                "contain clock rate information to generated a time array."
            )

        if time_dset_path not in self:
            raise ValueError(
                "The HDF5 file does NOT contain the time series dataset, "
                f"{time_dset_path}."
            )

        return self[time_dset_path][...]

    def read_controls(
        self,
        controls: List[str | Tuple[str, Any]],
        shotnum=slice(None),
        intersection_set=True,
        silent=False,
        **kwargs,
    ) -> HDFReadControls:
        """
        Reads data from control device datasets.  See
        `~.hdfreadcontrols.HDFReadControls` for more detail.

        Parameters
        ----------
        controls : List[str | Tuple[str, Any]]
            A list of strings and/or 2-element tuples indicating the
            control device(s).  If a control device has only one
            configuration then only the device name ``'control'`` needs
            to be passed in the list.  If a control device has multiple
            configurations, then the device name and its configuration
            "name" needs to be passed as a tuple element
            ``('control', 'config')`` in the list. (see
            :func:`~.helpers.condition_controls` for details)

        shotnum : int | list(int) | slice() | numpy.array, optional
            HDF5 file shot number(s) indicating data entries to be
            extracted

        intersection_set : `bool`, optional
            `True` (DEFAULT) will force the returned shot numbers to be
            the intersection of ``shotnum`` and the shot numbers
            contained in each control device dataset. `False` will
            return the union instead of the intersection, minus
            :math:`shotnum \\le 0`. (see
            `~.hdfreadcontrols.HDFReadControls` for details)

        silent : bool, optional
            `False` (DEFAULT).  Set `True` to ignore any `BaPSFWarning`
             (soft-warnings)

        Returns
        -------
        `~.hdfreadcontrols.HDFReadControls`
            `structured numpy array
            <https://numpy.org/doc/stable/user/basics.rec.html>`_ of
            control device data

        Examples
        --------

        >>> # open HDF5 file
        >>> f = File('sample.hdf5')
        >>>
        >>> # list control devices
        >>> list(f.controls)
        ['6K Compumotor', 'Waveform']
        >>>
        >>> # list '6K Compumotor' configurations
        >>> list(f.controls['6K Compumotor'].configs)
        [2, 3]
        >>>
        >>> # extract all '6k Compumotor' data for configuration 3
        >>> cdata = f.read_controls([('6K Compumotor', 3)])
        >>> type(cdata)
        bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls
        >>>
        >>> # list 'Waveform' configurations
        >>> list(f.file_map.controls['Waveform'].configs)
        ['config01']
        >>>
        >>> # extract 'Waveform' data
        >>> cdata = f.read_controls(['Waveform'])
        >>> list(cdata.info['controls'])
        ['Waveform']
        >>>
        >>> # extract both 'Waveform' and '6K Compumotor'
        >>> controls = ['Waveform', ('6K Compumotor', 2)]
        >>> cdata = f.read_controls(controls)
        >>> list(cdata.info['controls'])
        ['6K Compumotor', 'Waveform']

        """
        # to avoid cyclical imports
        from bapsflib._hdf.utils.hdfreadcontrols import HDFReadControls

        warn_filter = "ignore" if silent else "default"
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter, category=BaPSFWarning)
            data = HDFReadControls(
                self,
                controls,
                shotnum=shotnum,
                intersection_set=intersection_set,
                **kwargs,
            )

        return data

    def read_data(
        self,
        board: int,
        channel: int,
        index=slice(None),
        shotnum=slice(None),
        time_slice: slice = slice(None),
        digitizer=None,
        adc=None,
        config_name=None,
        keep_bits=False,
        add_controls=None,
        intersection_set=True,
        silent=False,
        **kwargs,
    ) -> HDFReadData:
        """
        Reads data from digitizer datasets and attaches control device
        data when requested.

        Parameters
        ----------
        board : `int`
            Analog-digital-converter board number

        channel : `int`
            Analog-digital-converter channel number

        index : int | list(int) | slice() | numpy.array, optional
            (DEFAULT: ``slice(None)``) Dataset row indices to be
            readout. Overridden by argument ``shotnum``.

        shotnum : int | list(int) | slice() | numpy.array, optional
            (DEFAULT: ``slice(None)``) HDF5 file shot number(s)
            indicating data entries to be extracted.  Overrides
            argument ``index``.

        time_slice : slice, optional
            (DEFAULT: ``slice(None)``) A `slice` object representing
            the time slice to be extracted from the digitizer dataset.

        digitizer : `str`, optional
            (DEFAULT: `None`) Name of digitizer

        adc : `str`, optional
            (DEFAULT: `None`) Name of the digitizer's
            analog-digital converter

        config_name : `str`, optional
            (DEFAULT: `None`) Name of digitizer configuration

        keep_bits : `bool`, optional
            (DEFAULT: `False`) Set `True` to keep the extracted data as
            is (i.e. in bits). Set `False` to convert the extracted data
            to voltage using stored meta-data in the associated header
            dataset.

        add_controls : List[str | Tuple[str, Any]], optional
            (DEFAULT: `None`) A list of strings and/or 2-element tuples
            indicating the control device(s).  If a control device has
            only one configuration, then only the device name
            ``'control'`` needs to be passed in the list.  If a control
            device has multiple configurations, then the device name
            and its configuration "name" needs to be passed as a tuple
            element ``('control', 'config')`` in the list. (see
            :func:`~.helpers.condition_controls` for details)

        intersection_set : `bool`, optional
            (DEFAULT: `True`) `True` will force the returned shot
            numbers to be the intersection of ``shotnum``, the digitizer
            dataset shot numbers, and, if requested, the shot numbers
            contained in  each control device dataset. `False` will
            return the union instead of the intersection, minus
            :math:`shotnum \\le 0`. (see `~.hdfreaddata.HDFReadData`
            for details)

        silent : `bool`, optional
            (DEFAULT: `False`) Set `True` to ignore any issued
            `~bapsflib.utils.warnings.BaPSFWarning`.

        Returns
        -------
        `~.hdfreaddata.HDFReadData`
            `structured numpy array
            <https://numpy.org/doc/stable/user/basics.rec.html>`_ of
            digitized data

        See Also
        --------
        ~bapsflib._hdf.utils.hdfreaddata.HDFReadData,
        ~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls

        Notes
        -----

        .. note::

            The ``shotnum`` keyword will always override the ``index``
            keyword, but, due to extra overhead required for identifying
            shot number locations in the digitizer dataset, the
            ``index`` keyword will always execute quicker than the
            ``shotnum`` keyword.

        Examples
        --------

        To read data associated with a digitizer there are 5 descriptors
        needed to fully define what data is to be extracted.  These
        descriptors are ``board``, ``channel``, ``digitizer``,
        ``config_name``, and ``adc``.  In the following example, board
        1, channel 2 will be read for the ``"SIS crate"`` digitizer
        on the ``"SIS 3302"`` analog-digital-converter for the
        ``"config01"`` digitizer configuration.

        >>> # open HDF5 file
        >>> f = File("sample.hdf5")
        >>>
        >>> # print detail about the mapped digitizers
        >>> print(f.digitizers)
        | Digitizer   | Configuration | ADC        | (board, [channel, ...]) | Shot Num. Range | nt   |
        +-------------+---------------+------------+-------------------------+-----------------+------+
        | 'SIS crate' | 'config01'    | 'SIS 3302' | (1, (2, 3, 4))          | ??              | 2500 |
        |             |---------------|------------|-------------------------|-----------------|------|
        |             | 'config02'    | 'SIS 3302' | (1, (2, 3, 4))          | ??              | 2500 |
        |             |               | 'SIS 3305' | (1, (1,))               | ??              | 2500 |

        >>>
        >>> # get data for brd = 1, ch = 2
        >>> data = f.read_data(
        ...     1,
        ...     2,
        ...     digitizer="SIS crate",
        ...     adc="SIS 3302",
        ...     config_name="config01",
        ... )
        >>> type(data)
        bapsflib._hdf.utils.hdfreaddata.HDFReadData

        The ``digitizer``, ``config_name``, and ``adc`` arguments
        are optional if there is only one value for each of those.  In
        this example ``digitizer`` is singular and ``adc`` is singular
        for configuration ``'config01'``, so only the configuration name
        (in addition to board and channel) needs to be specified.

        >>> data = f.read_data(1, 2, config_name="config01")

        ``data`` in this case will be a structured `numpy` array
        containing at leaset three fields: ``"shotnum"``, ``"signal"``,
        and ``"xyz"``.  ``'shotnum'`` is the array of shot numbers
        associated with the digitized data; ``"signal"`` is the acutal
        digitized data; and ``"zyz"`` is the probe xyz location.  The
        later is NaN at the moment, since positional data read-out has
        not been requested.

        >>> data.dtype
        dtype([('shotnum', '<u4'), ('signal', '<f4', (2500,)),
              ('xyz', '<f4', (3,))])
        >>>
        >>> # display shot numbers
        >>> data["shotnum"]
        array([  1,  2, ..., 98, 99], dtype=uint32)
        >>>
        >>> # show 'signal' values for shot number 1
        >>> data["signal"][0]
        array([-0.41381955, -0.4134333 , -0.4118886 , ..., -0.41127062,
               -0.4105754 , -0.41119337], dtype=float32)
        >>>
        >>> # show 'xyz' values for shot number 1
        >>> data["xyz"][0]
        array([nan, nan, nan], dtype=float32)

        If it is desired to read out only certain digitized traces, then
        this can be achieved with either the ``index`` or ``shotnum``
        argument, with the later taking precedence.

        >>> # get the first 5 traces using index
        >>> data = f.read_data(1, 2, config_name="config01", index=slice(5))
        >>> data = f.read_data(1, 2, config_name="config01", index=np.s_[:5])
        >>>
        >>> # get every 10th shot using shotnum
        >>> data = f.read_data(1, 2, config_name="config01", shotnum=slice(10, None, 10))
        >>> data = f.read_data(1, 2, config_name="config01", shotnum=np.s_[10::10])

        Sometimes only a certain time slice is desired, and this can
        be achieved using the ``time_slice`` arguemnt.

        >>> # get time subset
        >>> data = f.read_data(
        ...     1,
        ...     2,
        ...     config_name="config01",
        ...     time_slice=slice(200, 500, 1),
        ... )
        >>> data = f.read_data(
        ...     1,
        ...     2,
        ...     config_name="config01",
        ...     time_slice=np.s_[200:500:1],
        ... )
        >>>
        >>> # time_slice can be used with index or shotnum
        >>> data = HDFReadData(
        ...     f,
        ...     1,
        ...     2,
        ...     config_name="config01",
        ...     time_slice=slice(200, 500, 1),
        ...     shotnum=slice(10, None, 10),
        ... )
        >>> data = HDFReadData(
        ...     f,
        ...     1,
        ...     2,
        ...     config_name="config01",
        ...     time_slice=slice(200, 500, 1),
        ...     index=np.s_[0:5],
        ... )

        Now lets add position data to the read out.  Position data is
        recorded by control devices.  For this example lets assume
        the position data was recored by the ``"6K Compumotor"`` control
        device using the probe drive attached to receptical 3.  This
        information can be given using the ``add_controls`` argument.

        >>> # read digitizer data while adding '6K Compumotor' data
        >>> # from receptacle (configuration) 3
        >>> data = f.read_data(
        ...     1,
        ...     2,
        ...     config_name="config01",
        ...     add_controls=[("6K Compumotor", 3)],
        ... )
        >>> data.dtype
        dtype([('shotnum', '<u4'), ('signal', '<f4', (2500,)),
               ('xyz', '<f4', (3,)), ('ptip_rot_theta', '<f8'),
               ('ptip_rot_phi', '<f8')])
        >>>
        >>> # show 'xyz' values for shot number 1
        >>> data["xyz"][0]
        array([ -32. ,   15. , 1022.4], dtype=float32)

        Now the ``"xyz"`` is populated with position data, but
        additional fields (``"ptip_rot_theta"`` and ``"ptip_rot_phi"``)
        are added to the sturctured `numpy` array.  Each control device
        can add its own data fields to the array.  And, multiple
        control devices can be specified at the time of the data read.

        """
        # to avoid cyclical imports
        from bapsflib._hdf.utils.hdfreaddata import HDFReadData

        warn_filter = "ignore" if silent else "default"
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter, category=BaPSFWarning)
            data = HDFReadData(
                self,
                board,
                channel,
                index=index,
                shotnum=shotnum,
                time_slice=time_slice,
                digitizer=digitizer,
                adc=adc,
                config_name=config_name,
                keep_bits=keep_bits,
                add_controls=add_controls,
                intersection_set=intersection_set,
                **kwargs,
            )

        return data

    def read_msi(self, msi_diag: str, silent=False, **kwargs) -> HDFReadMSI:
        """
        Reads data from MSI Diagnostic datasets.  See
        `~.hdfreadmsi.HDFReadMSI` for more detail.

        Parameters
        ----------
        msi_diag : `str`
            name of MSI diagnostic

        silent : `bool`, optional
            `False` (DEFAULT).  Set `True` to ignore any `BaPSFWarning`
            (soft-warnings)

        Returns
        -------
        `~.hdfreadmsi.HDFReadMSI`
            `structured numpy array
            <https://numpy.org/doc/stable/user/basics.rec.html>`_ of
            MSI diagnostic data

        Examples
        --------

        >>> # open HDF5 file
        >>> f = File('sample.hdf5')
        >>>
        >>> # list msi diagnostics
        >>> list(f.msi)
        ['Interferometer array', 'Magnetic field']
        >>>
        >>> # read 'Interferometer array'
        >>> mdata = f.read_msi('Interferometer array')
        >>> type(mdata)
        bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI
        """
        from bapsflib._hdf.utils.hdfreadmsi import HDFReadMSI

        warn_filter = "ignore" if silent else "default"
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter, category=BaPSFWarning)
            data = HDFReadMSI(self, msi_diag, **kwargs)

        return data
