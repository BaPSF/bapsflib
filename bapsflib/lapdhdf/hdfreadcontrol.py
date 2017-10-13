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
                index=None, shotnum=None, silent=False, **kwargs):
        """
        When inheriting from numpy, the object creation and
        initialization is handled by __new__ instead of __init__.

        :param hdf_file:
        :param controls:
        :param index: dataset index/indices of data entries to be
            extracted
        :type index: :code:`None`, int, list(int), or
            slice(start, stop, skip)
        :param shotnum: HDF5 file shot number(s) indicating data
            entries to be extracted (:code:`shotnum` will take
            precedence over :code:`index`)
        :type shotnum: :code:`None`, int, list(int), or
            slice(start, stop, skip)
        :param bool silent:
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
        #   3. Condition 'controls' argument
        #   4. look for 'controls' in file_map.controls
        #   5. condition index keyword
        #   6. build recarray
        #   7. build obj.info (metadata)

        # initiate warning string
        warn_str = ''

        # -- Condition hdf_file --
        # Check hdf_file is a lapdhdf.File object
        if not (isinstance(hdf_file, h5py.File)
                and hasattr(hdf_file, 'file_map')):
            raise TypeError("hdf_file needs to be of type lapdhdf.File")

        # Check for non-empty controls
        if not hdf_file.file_map.controls \
                or hdf_file.file_map.controls is None:
            print('** Warning: There are no control devices in the HDF5'
                  ' file.')
            return None

        # -- Condition 'controls' Argument --
        # condition elements of 'controls' argument
        # - Controls is a list where elemnts cna be:
        #   1. a string indicating the name of a control device
        #   2. a 2-element tuple where the 1st entry is a string
        #      indicating the name of a control device and the 2nd is
        #      a unique specifier for that control device
        #
        if isinstance(controls, list):
            for ii, val in enumerate(controls):
                if type(val) is str:
                    if val not in hdf_file.file_map.controls:
                        del(controls[ii])
                elif type(val) is tuple:
                    if len(val) != 2:
                        del(controls[ii])
                    elif type(val[0]) is not str:
                        del(controls[ii])
                    elif val[0] not in hdf_file.file_map.controls:
                        del(controls[ii])
                else:
                    del(controls[ii])
        else:
            raise ValueError("improper 'controls' arg passed")

        # make sure 'controls' is not empty
        if not controls:
            raise ValueError("improper 'controls' arg passed")
        else:
            nControls = len(controls)

        # -- Condition index, shotnum, & shots Keywords --
        # shots   -- is for backwards compatibility but should not be
        #            used, it is the old name for the 'index' keyword
        # index   -- row index of dataset, indexed at 0, will supersede
        #            'shot' keyword, but 'shot' is just the old name for
        #            the 'index' keyword
        # shotnum -- global HDF5 file shot number, this is what is
        #            actually used to link values between datasets, this
        #            will supersede any other indexing keyword
        #
        # - Indexing behavior:
        #   ~ regardless of which keyword is used, datasets will always
        #     be matched using the global shot number (shotnum) index
        #   ~ if multiple 'controls' are specified and a specific
        #     shotnum is not in all specified 'controls', then that
        #     shotnum will be omitted from the output dataset
        #
        # 'shots' backwards compatibility
        # - 'shots' keyword which was renamed to 'index' in v0.1.3.dev1
        # - keyword 'index' will always take precedence over 'shots'
        #   keyword
        #
        if 'shots' in kwargs and index is None:
            index = kwargs['shots']

        # Determine min rows and shared shot numbers of all control
        # datasets
        #
        rowlen = None
        shotnumarr = None
        for control in controls:
            # control name and unique specifier
            if type(control) is tuple:
                cname = control[0]
                cspec = control[1]
            else:
                cname = control
                cspec = None

            # get control dataset
            cdset_name = hdf_file.file_map.controls[
                cname].construct_dataset_name(cspec)
            cdset_path = hdf_file.file_map.controls[cname].info[
                'group path'] + '/' + cdset_name
            cdset = hdf_file.get(cdset_path)
            shotnumkey = cdset.dtype.names[0]

            # Determine min rows
            if rowlen is None:
                rowlen = cdset[shotnumkey].shape[0]
            else:
                rowlen = min(rowlen, cdset[shotnumkey].shape[0])
            print(rowlen)

            # Determine shot number intersection of all control datasets
            if shotnumarr is None:
                shotnumarr = cdset[shotnumkey].view()
            else:
                shotnumarr = np.intersect1d(shotnumarr,
                                            cdset[shotnumkey].view(),
                                            assume_unique=True)

        # Ensure 'index' is a valid
        # - Valid index types are: None, int, list(int), and slice()
        #     None      => extract all indices
        #     int       => extract shot with index int
        #     list(int) => extract shots with indices specified in list
        #     slice(start, stop, skip)
        #               = > same as [start:stop:skip]
        #
        # if index is None:
        #     index = slice(None, None, None)
        #
        if shotnum is not None:
            # ignore index keyword if shotnum is used
            pass
        elif index is None:
            # defualt to shotnum keyword
            pass
        elif type(index) is int:
            if not (index in range(rowlen)
                    or -index - 1 in range(rowlen)):
                raise ValueError(
                    'index is not in range({})'.format(rowlen))
        elif type(index) is list:
            # all elements need to be integers
            if all(isinstance(s, int) for s in index):
                # condition list
                index.sort()
                index = list(set(index))
                newindex = []
                for s in index:
                    if s < 0:
                        s = -s - 1
                    if s in range(rowlen):
                        if s not in newindex:
                            newindex.append(s)
                    else:
                        warn_str += (
                            '\n** Warning: shot {} not a '.format(s)
                            + 'valid index, range({})'.format(rowlen))
                newindex.sort()

                if len(newindex) != 0:
                    index = newindex
                else:
                    raise ValueError('index: none of the elements are '
                                     'in range({})'.format(rowlen))
            else:
                raise ValueError("index keyword needs to be None, int, "
                                 "list(int), or slice object")
        elif type(index) is slice:
            # valid type
            pass
        else:
            raise ValueError("index keyword needs to be None, int, "
                             "list(int), or slice object")

        # Ensure 'shotnum' is valid
        #
        # TODO: pickup here

        # Construct obj
        # - obj will be a numpy record array
        #
        # - 1st column of the digi data header contains the global HDF5
        #   file shot number
        # - shotkey = is the field name/key of the dheader shot number
        #   column
        '''
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
        '''
        obj = shotnumarr.view(cls)

        # assign dataset info
        # TODO: add a dict key for each control w/ controls config
        # - control config dict should include:
        #   ~ 'contype'
        #   ~ 'dataset name'
        #   ~ 'dataset path'
        #
        obj.info = {
            'hdf file': hdf_file.filename.split('/')[-1],
            'controls': controls,
            'probe name': None,
            'port': (None, None)}

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
                             'controls': None,
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
