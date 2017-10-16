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
    # - if multiple controls are specified then,
    #   ~ only one control of each contype can be in the list of
    #     controls
    #   ~ if a specified control does not exist in the HDF5 file, then
    #     it will be deleted from the specified 'controls' list
    #   ~ the returned structured array will only contain intersecting
    #     HDF5 shot numbers (i.e. shot numbers that are included in
    #     all specified control datasets)
    #   ~ then, those intersecting shot numbers are filtered according
    #     to the index and shotnum keywords
    #
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

        # ---- Condition hdf_file ----
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

        # ---- Condition 'controls' Argument ----
        # condition elements of 'controls' argument
        # - Controls is a list where elements can be:
        #   1. a string indicating the name of a control device
        #   2. a 2-element tuple where the 1st entry is a string
        #      indicating the name of a control device and the 2nd is
        #      a unique specifier for that control device
        # - there can only be one control device per contype
        #
        controls = condition_controls(hdf_file, controls)

        # make sure 'controls' is not empty
        if not controls:
            raise ValueError("improper 'controls' arg passed")
        else:
            nControls = len(controls)

        # ---- Condition index, shotnum, & shots Keywords ----
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

        # Determine shared shot numbers of all control datasets
        #
        #rowlen = None
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
            # if rowlen is None:
            #     rowlen = cdset[shotnumkey].shape[0]
            # else:
            #     rowlen = min(rowlen, cdset[shotnumkey].shape[0])

            # Determine shot number intersection of all control datasets
            if shotnumarr is None:
                shotnumarr = cdset[shotnumkey].view()
            else:
                shotnumarr = np.intersect1d(shotnumarr,
                                            cdset[shotnumkey].view(),
                                            assume_unique=True)

        # Determine min row length
        rowlen = shotnumarr.shape[0]

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
            index = None
            pass
        elif index is None:
            # default to shotnum keyword
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
        if index is not None:
            # - index conditioning should ensure index is not None only
            #   if shotnum is not specified (i.e. shotnum is None and
            #   index is not None)
            # - translate index keyword to shotnum keyword...the
            #   remainder of this routine will utilized shotnum only
            #
            shotnum = shotnumarr[index].view()
        elif shotnum is None:
            # assume all intersecting entries are desired
            shotnum = shotnumarr.view()
        elif type(shotnum) is int:
            shotnum = np.array(shotnum).view()
            if shotnum not in shotnumarr:
                raise ValueError('shotnum [{}]'.format(shotnum)
                                 + ' is not a valid shot number')
        elif type(shotnum) is list:
            shotnum = np.intersect1d(shotnum, shotnumarr).view()
            if shotnum.shape[0] == 0:
                raise ValueError('Valid shotnum not passed')
        elif type(shotnum) is slice:
            shotnum = np.intersect1d(
                np.arange(shotnum.start, shotnum.stop, shotnum.step),
                shotnumarr).view()
            if shotnum.shape[0] ==0:
                raise ValueError('Valid shotnum not passed')
        else:
            raise ValueError('Valid shotnum not passed')

        # ---- Build obj ----
        # Determine fields for numpy array
        npfields = {}
        for control in controls:
            if type(control) is tuple:
                control = control[0]

            conmap = hdf_file.file_map.controls[control]
            for df_name, nf_name, npi \
                    in conmap.config['dset field to numpy field']:
                if nf_name == 'shotnum':
                    # already in dtype
                    pass
                elif nf_name in npfields:
                    npfields[nf_name][1] += 1
                else:
                    npfields[nf_name] = ['<f8', 1]

        # Define dtype and shape for numpy array
        odytpe = [('shotnum', '<u4')]
        for key in npfields:
            if npfields[key][1] == 1:
                odytpe.append((key, npfields[key][0]))
            else:
                odytpe.append((key, npfields[key][0], npfields[key][1]))
        shape = shotnum.shape

        # Initialize Control Data
        data = np.empty(shape, dtype=odytpe)
        data['shotnum'] = shotnum.view()

        # Assign Control Data to Numpy array
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

            # get indices for desired shot numbers
            # - How to find shotnum indices
            #   1. let arr1 be the shotnum array you want to filter
            #   2. let arr2 be the list of shotnums you want
            #      (hence shotnumarr)
            #   3. numpy.in1d(arr1, arr2) will return a boolean array
            #      of shape arr1.shape with shared valued entries being
            #      True
            #   4. numpy.in1d(arr1, arr2).nonzero() will return an array
            #      of indices where numpy.ind1d() is True
            #
            shoti = np.in1d(cdset[shotnumkey], shotnum).nonzero()

            # assign values
            conmap = hdf_file.file_map.controls[cname]
            for df_name, nf_name, npi \
                    in conmap.config['dset field to numpy field']:
                if nf_name != 'shotnum':
                    data[nf_name][..., npi] = cdset[df_name][shoti]

        # How to find shotnum indices
        # - let arr1 be the shotnum array you want to filter
        # - let arr2 be the list of shotnums you want (hence shotnumarr)
        # - numpy.in1d(arr1, arr2) will return a boolean array of shape
        #   arr1.shape with shared valued entries being True
        # - numpy.in1d(arr1, arr2).nonzero() will return an array of
        #   indices where numpy.ind1d() is True

        # Construct obj
        obj = data.view(cls)
        # if type(shotnum) is np.int32:
        #    obj = np.array([shotnum]).view(cls)
        # else:
        #    obj = shotnum.view(cls)

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


def condition_controls(hdf_file, controls):
    # Check hdf_file is a lapdhdf.File object
    if not (isinstance(hdf_file, h5py.File)
            and hasattr(hdf_file, 'file_map')):
        raise TypeError("hdf_file needs to be of type lapdhdf.File")

    # Check for non-empty controls
    if not hdf_file.file_map.controls \
            or hdf_file.file_map.controls is None:
        print('** Warning: There are no control devices in the HDF5'
              ' file.')
        return []

    # condition elements of 'controls' argument
    # - Controls is a list where elements can be:
    #   1. a string indicating the name of a control device
    #   2. a 2-element tuple where the 1st entry is a string
    #      indicating the name of a control device and the 2nd is
    #      a unique specifier for that control device
    #
    if isinstance(controls, list):
        for ii, device in enumerate(controls):
            if type(device) is str:
                if device not in hdf_file.file_map.controls:
                    del (controls[ii])
            elif type(device) is tuple:
                if len(device) != 2:
                    del (controls[ii])
                elif type(device[0]) is not str:
                    del (controls[ii])
                elif device[0] not in hdf_file.file_map.controls:
                    del (controls[ii])
            else:
                del (controls[ii])
    else:
        controls = []

    # enforce one device per contype
    checked = []
    for device in controls:
        contype = hdf_file.file_map.controls[device].contype
        if contype in checked:
            controls = []
            print('** Warning: Multiple devices per contype')
            break
        else:
            checked.append(contype)

    # return conditioned list
    return controls


