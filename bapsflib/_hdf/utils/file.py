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
import os
import warnings

# from bapsflib.lapd._hdf.hdfoverview import hdfOverview
from bapsflib._hdf.maps.hdfmap import HDFMap
from warnings import warn


class File(h5py.File):
    """
    Open a HDF5 file created at the Basic Plasma Science Facility.

    All functionality of :class:`h5py.File` is preserved (for detials
    see http://docs.h5py.org/en/latest/)
    """

    """
    :param driver: File driver to use
    :param libver: Compatibility bounds
    :param userblock_size: Size (in bytes) of the user block. If
        nonzero, must be a power of 2 and at least 512.
    :param swmr: Single Write, Multiple Read
    :param kwargs: Driver specific keywords
    """
    def __init__(self, name: str, mode='r',
                 control_path='/', digitizer_path='/', msi_path='/',
                 silent=False, **kwargs):
        """
        :param name: name (and path) of file on disk
        :param mode: readonly :code:`'r'` (DEFAULT) and read/write
            :code:`'r+'`
        :param control_path: internal HDF5 path to group containing
            control devices
        :param digitizer_path: internal HDF5 path to group containing
            digitizer devices
        :param msi_path: internal HDF5 path to group containing MSI
            devices
        :param silent: set :code:`True` to suppress warnings
            (:code:`False` DEFAULT)
        :param kwargs:  additional keywords passed on to
            :class:`h5py.File`
        """
        # initialize
        if mode not in ('r', 'r+'):
            warn("Only modes readonly 'r' and read/wrie 'r+' are "
                 "supported.  Opening as readonly.")
            mode = 'r'
        kwargs['mode'] = mode
        h5py.File.__init__(self, name, **kwargs)

        # -- define device paths --
        #: Internal HDF5 path for control devices. (DEFAULT :code:`'/'`)
        self.CONTROL_PATH = control_path

        #: Internal HDF5 path for digitizer devices.
        #: (DEFAULT :code:`'/'`)
        self.DIGITIZER_PATH = digitizer_path

        #: Internal HDF5 path for MSI devices. (DEFAULT :code:`'/'`)
        self.MSI_PATH = msi_path

        # -- map and build info --
        warn_filter = "ignore" if silent else "default"
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter)

            # create map
            self._map_file()

            # build `_info` attribute
            self._build_info()

    def _build_info(self):
        """Builds the general info dictionary for the file"""
        # define file keys
        self._info = {
            'file': os.path.basename(self.filename),
            'absolute file path': os.path.abspath(self.filename),
        }

        # add run info
        # self._info.update(self.file_map.run_info)

        # add exp info
        # self._info.update(self.file_map.exp_info)

    def _map_file(self):
        """Map/re-map the HDF5 file."""
        self._file_map = HDFMap(
            self,
            control_path=self.CONTROL_PATH,
            digitizer_path=self.DIGITIZER_PATH,
            msi_path=self.MSI_PATH)

    @property
    def controls(self):
        """Dictionary of control device mappings."""
        return self.file_map.controls

    @property
    def digitizers(self):
        """Dictionary of digitizer device mappings"""
        return self.file_map.digitizers

    @property
    def file_map(self):
        """HDF5 file map"""
        return self._file_map

    @property
    def info(self):
        """
        Dictionary of general info on the HDF5 file and experimental
        run.
        """
        return self._info

    @property
    def msi(self):
        """Dictionary of MSI device mappings."""
        return self.file_map.msi

    '''
    @property
    def overview(self):
        """
        HDF5 file overview. (Instance of
        :class:`~bapsflib.lapd.hdfoverview.hdfOverview`)
        """
        return hdfOverview(self)
    '''

    def read_controls(self, controls,
                      shotnum=slice(None),
                      intersection_set=True,
                      silent=False, **kwargs):
        """
        Reads data out of control device datasets.  See
        :class:`~bapsflib.lapd.hdfreadcontrol.HDFReadControl` for
        more detail.

        :param controls: a list of strings and/or 2-element tuples
            indicating the control device(s). (see
            :class:`~bapsflib.lapd.hdfreadcontrol.HDFReadControl`
            for details)
        :type controls: [str, (str, val), ]
        :param shotnum: HDF5 file shot number(s) indicating data
            entries to be extracted
        :type shotnum: int, list(int), slice()
        :param bool intersection_set: :code:`True` (DEFAULT) will force
            the returned shot numbers to be the intersection of
            :data:`shotnum` and the shot numbers contained in each
            control device dataset. :code:`False` will return the union
            instead of the intersection  (see
            :class:`~bapsflib.lapd.hdfreadcontrol.HDFReadControl`
            for details)
        :param bool silent: :code:`False` (DEFAULT).  Set :code:`True`
            to suppress command line printout of soft-warnings
        :return: extracted data from control device(s)
        :rtype: :class:`~bapsflib.lapd.hdfreadcontrol.HDFReadControl`

        :Example:

            >>> # open HDF5 file
            >>> f = File('sample.hdf5')
            >>>
            >>> # list control devices
            >>> f.list_controls
            ['6K Compumotor', 'Waveform']
            >>>
            >>> # list '6K Compumotor' configurations
            >>> list(f.file_map.controls['6K Compumotor'].configs)
            [2, 3]
            >>>
            >>> # extract all '6k Compumotor', configuration 3 data
            >>> cdata = f.read_controls([('6K Compumotor', 3)])
            >>>
            >>> # list 'Waveform' configurations
            >>> list(f.file_map.controls['Waveform'].configs)
            ['config01']
            >>>
            >>> # extract 'Waveform' data
            >>> cdata = f.read_controls(['Waveform'])
            >>>
            >>> # extract both 'Waveform' and '6K Compumotor'
            >>> controls = ['Waveform', ('6K Compumotor', 2)]
            >>> cdata = f.read_controls(controls)

        """
        from bapsflib._hdf.utils.hdfreadcontrol import HDFReadControl

        warn_filter = 'ignore' if silent else 'default'
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter)
            data = HDFReadControl(self, controls,
                                  shotnum=shotnum,
                                  intersection_set=intersection_set,
                                  **kwargs)

        return data

    def read_data(self, board, channel,
                  index=slice(None), shotnum=slice(None),
                  digitizer=None, adc=None,
                  config_name=None, keep_bits=False, add_controls=None,
                  intersection_set=True, silent=False,
                  **kwargs):
        # TODO: docstrings and code block needs updating
        """
        Provides access to
        :class:`~bapsflib.lapd.hdfreaddata.HDFReadData` to extract
        data from a specified digitizer dataset in the HDF5 file and,
        if requested, mate control device data to the extracted
        digitizer data. See
        :class:`~bapsflib.lapd.hdfreaddata.HDFReadData` for more
        detail.

        :param int board: digitizer board number
        :param int channel: digitizer channel number
        :param index: dataset row index
        :type index: int, list(int), slice()
        :param shotnum: HDF5 global shot number
        :type shotnum: int, list(int), slice()
        :param str digitizer: name of digitizer
        :param str adc: name of the digitizer's analog-digital converter
        :param str config_name: name of digitizer configuration
        :param bool keep_bits: :code:`True` for output in bits,
            :code:`False` (default) for output in voltage
        :param add_controls: a list of strings and/or 2-element tuples
            indicating control device data to be mated to the digitizer
            data. (see
            :class:`~bapsflib.lapd.hdfreaddata.HDFReadData`
            for details)
        :type add_controls: [str, (str, val), ]
        :param bool intersection_set: :code:`True` (default) forces the
            returned array to only contain shot numbers that are in the
            intersection of :data:`shotnum`, the digitizer dataset, and
            all the control device datasets. (see
            :class:`~bapsflib.lapd.hdfreaddata.HDFReadData`
            for details)
        :param bool silent: :code:`False` (default). Set :code:`True` to
            suppress command line printout of soft-warnings
        :return: extracted data from digitizer (and control devices)
        :rtype: :class:`~bapsflib.lapd.hdfreaddata.HDFReadData`
        """
        #
        # :param add_controls: a list of strings and/or 2-element tuples
        #     indicating control device data to be mated to the
        #     digitizer data. If an element is a string, then that
        #     string is the name of the control device, If an element is
        #     a 2-element tuple, then the 1st element is the name of the
        #     control device and the 2nd element is a unique specifier
        #     for that control device.
        # :param intersection_set: :code:`True` (default) ensures the
        #     returned array only contains shot numbers that are found
        #     in the digitizer dataset and all added control device
        #     datasets. :code:`False` will cause the returned array to
        #     contain shot numbers specified by :data:`shotnum` or, when
        #     :data:`index` is used, the matching shot numbers in the
        #     digitizer dataset specified by :data:`index`
        #
        # TODO: write docstrings
        #
        from bapsflib._hdf.utils.hdfreaddata import HDFReadData

        warn_filter = 'ignore' if silent else 'default'
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter)
            data = HDFReadData(self, board, channel,
                               index=index,
                               shotnum=shotnum,
                               digitizer=digitizer,
                               adc=adc,
                               config_name=config_name,
                               keep_bits=keep_bits,
                               add_controls=add_controls,
                               intersection_set=intersection_set,
                               **kwargs)

        return data

    def read_msi(self, msi_diag, silent=False, **kwargs):
        """
        Reads data out for a MSI Diagnostic.  See
        :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI` for more
        detail.

        :param str msi_diag: name of MSI diagnostic
        :param bool silent:
        :return: data for MSI diagnostic
        :rtype: :class:`~bapsflib._hdf.utils.hdfreadmsi.HDFReadMSI`

        :Example:

            >>> import numpy as np
            >>>
            >>> # open HDF5 file
            >>> f = File('sample.hdf5')
            >>>
            >>> # list msi diagnostics
            >>> f.list_msi
            ['Interferometer array', 'Magnetic field']
            >>>
            >>> # read 'Interferometer array'
            >>> mdata = f.read_msi('Interferometer array')
            >>> isinstance(mdata, np.recarray)
            True

        """
        from bapsflib._hdf.utils.hdfreadmsi import HDFReadMSI

        warn_filter = 'ignore' if silent else 'default'
        with warnings.catch_warnings():
            warnings.simplefilter(warn_filter)
            data = HDFReadMSI(self, msi_diag, **kwargs)

        return data
