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
    Reads out control device data from the HDF5 file.
    """
    # .. note::
    #
    #     It is assumed that control data is always extracted with the
    #    intent of being matched to digitizer data
    #
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
                index=None, shotnum=None, intersection_set=True,
                silent=False, **kwargs):
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
        :param bool intersection_set:
        :param bool silent:
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
        #       controls = ['6K Compumotor', 'Waveform', 'N5700_PS']
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
        try:
            file_map = hdf_file.file_map
        except AttributeError:
            raise AttributeError(
                "hdf_file needs to be of type lapdhdf.File")

        # Check for non-empty controls
        if not file_map.controls or file_map.controls is None:
            raise ValueError(
                'There are no control devices in the HDF5 file.')

        # ---- Condition 'controls' Argument ----
        # condition elements of 'controls' argument
        # - Controls is a list where elements can be:
        #   1. a string indicating the name of a control device
        #   2. a 2-element tuple where the 1st entry is a string
        #      indicating the name of a control device and the 2nd is
        #      a unique specifier for that control device
        # - there can only be one control device per contype
        #
        controls = condition_controls(hdf_file, controls, silent=silent)

        # make sure 'controls' is not empty
        if not controls:
            raise ValueError("improper 'controls' arg passed")

        # ---- Condition index and shotnum Keywords ----
        # index   -- row index of dataset
        #            ~ indexed at 0
        #            ~ overridden by shotnum
        # shotnum -- global HDF5 file shot number
        #            ~ this is the index used to link values between
        #              datasets
        #            ~ supersedes any other indexing keyword
        #
        # - Indexing behavior: (depends on intersection_set)
        #
        #   ~ intersection_set = True
        #     * index
        #       > if len(controls) == 1, then index will be the dataset
        #         row index
        #       > if len(controls) > 1, then index will correspond to
        #         the index of the list of intersecting shot numbers of
        #         all specified control devices
        #     * shotnum
        #       > the returned array will only contain shot numbers that
        #         are in the intersection of shotnum and all the
        #         specified control device datasets
        #
        #   ~ intersection_set = False
        #     * index
        #       > index corresponds to the 1st dataset row index
        #       > if the 2nd and later datasets don't include the
        #         shotnum of the 1st dataset, then they will be given a
        #         numpy.nan value
        #     * shotnum
        #       > the returned array will contain all shot numbers
        #         specified by shotnum
        #       > if a dataset does not included a shot number contained
        #         in shotnum, then its entry in the returned array will
        #         be given a numpy.nan value
        #
        # dset_sn - 1D array of shotnum's that will be either the
        #           intersection of shot numbers of all control device
        #           datasets specified by controls (for
        #           intersection_set=True) or the shot numbers of the
        #           first control device dataset specified in controls
        #           (for intersection_set=False)
        # shotnum - regardless of if index or shotnum is specified,
        #           shotnum will be re-defined to include all shot
        #           numbers that will be placed into the obj array

        # Determine dset_sn and rowlen
        method = 'intersection' if intersection_set else 'first'
        dset_sn = gather_shotnums(hdf_file, controls, method=method)
        rowlen = dset_sn.shape[0]

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
            if all(type(s) is int for s in index):
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
        # - here 'shotnum' will be converted from its keyword type to a
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
        elif shotnum is None:
            # assume all intersecting entries are desired
            shotnum = dset_sn.view()
        elif type(shotnum) is int:
            if shotnum in dset_sn:
                shotnum = np.array([shotnum])
            else:
                raise ValueError('shotnum [{}] is not '.format(shotnum)
                                 + 'a valid shot number')
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
                if intersection_set:
                    shotnum = np.intersect1d(shotnum, dset_sn).view()
                else:
                    shotnum = np.array(shotnum).view()

                # ensure obj will not be a zero dim array
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
            if intersection_set:
                shotnum = np.intersect1d(
                    np.arange(shotnum.start,
                              shotnum.stop,
                              shotnum.step),
                    dset_sn).view()
            else:
                shotnum = np.arange(shotnum.start, shotnum.stop,
                                    shotnum.step)

            # ensure obj will not be a zero dim array
            if shotnum.shape[0] == 0:
                raise ValueError('Valid shotnum not passed')
        else:
            raise ValueError('Valid shotnum not passed')

        # ---- Build obj ----
        # Determine fields for numpy array
        # npfields - dictionary of structured array field names
        #            npfields['field name'] = [type, shape]
        #
        npfields = {}
        for control in controls:
            if type(control) is tuple:
                control = control[0]

            conmap = file_map.controls[control]
            for df_name, nf_name, npi \
                    in conmap.config['dset field to numpy field']:
                # df_name - control dataset field name
                # nf_name - numpy structured array field name
                # npi     - numpy index df_name will be inserted into
                if nf_name == 'shotnum':
                    # already in dtype
                    pass
                elif nf_name in npfields:
                    npfields[nf_name][1] += 1
                else:
                    npfields[nf_name] = ['<f8', 1]

        # Define dtype and shape for numpy array
        dytpe = [('shotnum', '<u4', 1)]
        for key in npfields:
            dytpe.append((key, npfields[key][0], npfields[key][1]))
        shape = shotnum.shape

        # Initialize Control Data
        data = np.empty(shape, dtype=dytpe)
        data['shotnum'] = shotnum.view()
        for field in npfields:
            data[field][:] = np.nan

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
            conmap = file_map.controls[cname]
            cdset_name = conmap.construct_dataset_name(cspec)
            cdset_path = conmap.info['group path'] + '/' + cdset_name
            cdset = hdf_file.get(cdset_path)
            shotnumkey = cdset.dtype.names[0]

            if intersection_set:
                # find cdset indices that match shotnum
                shoti = np.in1d(cdset[shotnumkey], shotnum)

                # assign values
                # df_name - device dataset field name
                # nf_name - corresponding numpy field name
                # npi     - numpy index that dataset will be assigned to
                #
                for df_name, nf_name, npi \
                        in conmap.config['dset field to numpy field']:
                    if nf_name != 'shotnum':
                        data[nf_name][:, npi] = \
                            cdset[df_name][shoti].view()
            else:
                # get intersecting shot numbers
                sn_intersect = np.intersect1d(cdset[shotnumkey],
                                              shotnum).view()
                datai = np.in1d(shotnum, sn_intersect)
                cdseti = np.in1d(cdset[shotnumkey], sn_intersect)

                # assign values
                # df_name - device dataset field name
                # nf_name - corresponding numpy field name
                # npi     - numpy index that dataset will be assigned to
                #
                for df_name, nf_name, npi \
                        in conmap.config['dset field to numpy field']:
                    if nf_name != 'shotnum':
                        data[nf_name][datai, npi] = \
                            cdset[df_name][cdseti].view()

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
            #shoti = np.in1d(cdset[shotnumkey], shotnum).nonzero()

            # assign values
            #conmap = file_map.controls[cname]
            #for df_name, nf_name, npi \
            #        in conmap.config['dset field to numpy field']:
            #    if nf_name != 'shotnum':
            #        data[nf_name][..., npi] = cdset[df_name][shoti]

        # Construct obj
        obj = data.view(cls)

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

        # print warnings
        if not silent:
            print(warn_str)

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


def condition_controls(hdf_file, controls, silent=False):
    # initialize warning string
    warn_str = ''

    # Check hdf_file is a lapdhdf.File object
    try:
        file_map = hdf_file.file_map
    except AttributeError:
        raise AttributeError(
            "hdf_file needs to be of type lapdhdf.File")

    # Check for non-empty controls
    if not file_map.controls or file_map.controls is None:
        if not silent:
            print('** Warning: There are no control devices in the HDF5'
                  ' file.')
        return []

    # condition elements of 'controls' argument
    # - controls is a list where elements can be:
    #   1. a string indicating the name of a control device
    #   2. a 2-element tuple where the 1st entry is a string
    #      indicating the name of a control device and the 2nd is
    #      a unique specifier for that control device
    #
    # - ensure
    #   1. controls is in agreement is defined format above
    #   2. all control device are in file_map.controls
    #   3. there are not duplicate devices in controls
    #
    if type(controls) is list:
        new_controls = []
        for device in controls:
            if type(device) is str:
                if device in file_map.controls \
                        and device not in new_controls:
                    new_controls.append(device)
            elif type(device) is tuple:
                try:
                    if len(device) == 2 \
                            and type(device[0]) is str \
                            and device[0] in file_map.controls \
                            and device not in new_controls:
                        new_controls.append(device)
                except IndexError:
                    pass
    else:
        new_controls = []

    # enforce one device per contype
    checked = []
    controls = new_controls
    for device in controls:
        contype = file_map.controls[device].contype
        if contype in checked:
            controls = []
            warn_str = '** Warning: Multiple devices per contype'
            break
        else:
            checked.append(contype)

    # print warnings
    if not silent:
        print(warn_str)

    # return conditioned list
    return controls


def gather_shotnums(hdf_file, controls, method='union'):
    # Check hdf_file is a lapdhdf.File object
    # controls = condition_controls(hdf_file, controls)

    # condition method keyword
    if method not in ['union', 'intersection', 'first']:
        return None

    # build array of shot numbers
    shotnumarr = None
    for device in controls:
        # control name and unique specifier
        if type(device) is tuple:
            cname = device[0]
            cspec = device[1]
        else:
            cname = device
            cspec = None

        # get control dataset
        cdset_name = hdf_file.file_map.controls[
            cname].construct_dataset_name(cspec)
        cdset_path = hdf_file.file_map.controls[cname].info[
            'group path'] + '/' + cdset_name
        cdset = hdf_file.get(cdset_path)
        shotnumkey = cdset.dtype.names[0]

        # Define shotnumarr
        if shotnumarr is None:
            # first assignment
            shotnumarr = cdset[shotnumkey].view()

            # break if only want shot numbers for first dataset
            if method == 'first':
                break
        elif method == 'intersection':
            # build set of intersecting shot numbers
            shotnumarr = np.intersect1d(shotnumarr,
                                        cdset[shotnumkey].view(),
                                        assume_unique=True)
        else:
            # method == 'union'
            shotnumarr = np.union1d(shotnumarr,
                                    cdset[shotnumkey].view())

    # return numpy array of intersecting shot numbers
    return shotnumarr
