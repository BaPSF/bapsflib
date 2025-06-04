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
"""
Helper functions that are utilized by the HDF5 utility classes defined
in module :mod:`bapsflib._hdf.utils`.
"""
__all__ = [
    "build_shotnum_dset_relation",
    "condition_controls",
    "condition_shotnum",
    "do_shotnum_intersection",
    "IndexDict",
]

import h5py
import numpy as np

from typing import Any, Dict, Iterable, List, Optional, Tuple

from bapsflib._hdf.utils.file import File

# define type aliases
IndexDict = Dict[str, Dict[str, np.ndarray]]


def build_shotnum_dset_relation(
    shotnum: np.ndarray,
    dset: h5py.Dataset,
    shotnumkey: str,
    n_configs: int,
    config_column_value: Any,
    config_column: Optional[str] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compares the ``shotnum`` `numpy` array to the specified dataset,
    ``dset``, to determine which indices contain the desired shot
    number(s)
    [for `~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls`].
    As a results, two numpy arrays are returned which satisfy the rule::

        shotnum[sni] = dset[index, shotnumkey]

    where ``shotnum`` is the original shot number array, ``sni`` is a
    boolean `numpy` array masking which shot numbers were determined to
    be in the dataset, and ``index`` is an array of indices
    corresponding to the desired shot number(s).

    Parameters
    ----------
    shotnum : :term:`array_like`
        Array like object of desired shot numbers.

    dset: `h5py.Dataset`
        Control device dataset

    shotnumkey : `str`
        Dataset field name containing shot numbers.

    n_configs : int
        The number of unique configurations contained in ``dset``.

    config_column_value : `Any`
        The configuration value to searched for in ``config_column``.
        This is typically the name of the device configuration.

    config_column : Optional[`str`]
        Name of the ``dset`` column containing control configurations.
        If omitted, then ``dset`` columns are searched for a name
        containing 'configuration'.  (DEFAULT: `None`)

    Returns
    -------
    index : `numpy.ndarray`
        array of indices to index ``dset``

    sni : `numpy.ndarray`
        boolean array that masks the ``shotnum`` array

    """
    # We assume the shot numbers in shotnum and dset are sequential.  If they
    # are not, then something wrong occurred with the ACQ II.
    #
    if shotnumkey not in dset.dtype.names:
        raise ValueError(
            f"The expected shot number column '{shotnumkey}' not found in the "
            f"HDF5 dataset {dset.name}.  Present columns are {dset.dtype.names}."
        )

    if config_column is None:
        # assume default column name
        column_name_mask = [
            "configuration" in name.casefold() for name in dset.dtype.names
        ]
        if np.count_nonzero(column_name_mask) > 1 or (
            np.count_nonzero(column_name_mask) != 1 and n_configs != 1
        ):
            raise ValueError(
                "No column configuration name given (i.e. config_column ==  None) "
                "and unable to infer configuration name from "
                f"HDF5 dataset ('{dset.name}') column names, {list(dset.dtype.names)}."
            )

        if np.count_nonzero(column_name_mask) == 1:  # n_configs == 1
            config_column = dset.dtype.names[np.where(column_name_mask)[0][0]]
        else:
            # n_configs == 1 and there's no configuration column...assume the
            # dataset represents a single configuration
            pass

    elif config_column not in dset.dtype.names:
        raise ValueError(
            f"The configuration column '{config_column}' not found in the "
            f"HDF5 dataset '{dset.name}'.  Present columns are {dset.dtype.names}."
        )

    dset_shotnum = dset[shotnumkey]
    if n_configs == 1 and dset_shotnum.size != np.unique(dset_shotnum).size:
        raise ValueError(
            f"HDF5 dataset {dset.name} is indicated to have a single configuration, "
            f"but the shot number column is NOT uniquely filled.  Indicating "
            f"multiple configurations are present."
        )

    if config_column is None:
        config_mask = np.ones_like(dset_shotnum, dtype=bool)
    else:
        dset_config_column = dset[config_column]  # type: np.ndarray
        config_mask = (
            dset_config_column == config_column_value.encode()
        )  # type: np.ndarray

        if np.count_nonzero(config_mask) == 0:
            raise ValueError(
                f"The config_column_value '{config_column_value}' could not be "
                f"found in the HDF5 dataset '{dset.name}'.  Valid values are "
                f"{np.unique(dset_config_column)}."
            )

    dset_shotnum_subset = dset_shotnum[config_mask]

    intersection, sni_index, dset_subset_index = np.intersect1d(
        shotnum, dset_shotnum_subset, assume_unique=True, return_indices=True
    )

    # construct sni
    sni = np.zeros_like(shotnum, dtype=bool)
    sni[sni_index] = True

    # construct index
    mask = np.zeros_like(dset_shotnum_subset, dtype=bool)
    mask[dset_subset_index] = True
    config_mask[config_mask] = mask
    index = np.where(config_mask)[0]

    if np.count_nonzero(sni) != index.size:  # coverage: ignore
        raise ValueError(
            "Something went wrong... The constructed 'sni' does NOT have the "
            "same number of True values as the size of the constructed 'index' "
            "array."
        )

    return index.view(), sni.view()


def condition_controls(hdf_file: File, controls: Any) -> List[Tuple[str, Any]]:
    """
    Conditions the ``controls`` argument for
    `~.hdfreadcontrols.HDFReadControls` and `~.hdfreaddata.HDFReadData`.

    Parameters
    ----------
    hdf_file : `~bapsflib._hdf.utils.file.File`
        HDF5 object instance

    controls :
        ``controls`` argument to be conditioned

    Returns
    -------
    `list`
        A `list` containing tuple pairs of control device name and desired
        configuration name

    Examples
    --------

    >>> from bapsflib import lapd
    >>> f = lapd.File('sample.hdf5')
    >>> controls = ['Wavefrom', ('6K Compumotor', 3)]
    >>> conditioned_controls = condition_controls(f, controls)
    >>> conditioned_controls
    [('Waveform', 'config01'), ('6K Compumotor', 3)]

    .. admonition:: Condition Criteria

        #. Input ``controls`` should be
           ``Union[str, Iterable[Union[str, Tuple[str, Any]]]]``
        #. There can only be one control for each
           :class:`~bapsflib._hdf.maps.controls.types.ConType`.
        #. If a control has multiple configurations, then one must be
           specified.
        #. If a control has ONLY ONE configuration, then that will be
           assumed (and checked against the specified configuration).
    """
    # grab instance of file mapping
    _fmap = hdf_file.file_map

    # -- condition 'controls' argument                              ----
    # - controls is:
    #   1. a string or Iterable
    #   2. each element is either a string or tuple
    #   3. if tuple, then length <= 2
    #      ('control name',) or ('control_name', config_name)
    #
    # check if NULL
    if not bool(controls):
        # catch a null controls
        raise ValueError("controls argument is NULL")

    # make string a list
    if isinstance(controls, str):
        controls = [controls]

    # condition Iterable
    if not isinstance(controls, Iterable):
        raise TypeError("`controls` argument is not Iterable")

    # all list items have to be strings or tuples
    if not all(isinstance(con, (str, tuple)) for con in controls):
        raise TypeError("all elements of `controls` must be of type string or tuple")

    # condition controls
    new_controls = []
    for control in controls:
        if isinstance(control, str):
            name = control
            config_name = None
        else:
            # tuple case
            if len(control) > 2:
                raise ValueError(
                    "a `controls` tuple element must be specified "
                    "as ('control name') or, "
                    "('control name', config_name)"
                )

            name = control[0]
            config_name = None if len(control) == 1 else control[1]

        # ensure proper control and configuration name are defined
        if name in [cc[0] for cc in new_controls]:
            raise ValueError(
                f"Control device ({control}) can only have one occurrence in controls"
            )
        elif name in _fmap.controls:
            control_map = _fmap.controls[name]

            if config_name is None and len(control_map.configs) == 1:
                config_name = list(control_map.configs)[0]
            else:
                config_name = control_map.process_config_name(config_name)

        else:
            raise ValueError(f"Control device ({name}) not in HDF5 file")

        # add control to new_controls
        new_controls.append((name, config_name))

    # re-assign `controls`
    controls = new_controls

    # enforce one control per contype
    checked = []
    for control in controls:
        # control is a tuple, not a string
        contype = _fmap.controls[control[0]].contype

        if contype in checked:
            raise TypeError("`controls` has multiple devices per contype")
        else:
            checked.append(contype)

    # return conditioned list
    return controls


def condition_shotnum(
    shotnum: Any, dset_list: List[h5py.Dataset], shotnumkey_list: List[str]
) -> np.ndarray:
    r"""
    Conditions the ``shotnum`` argument for
    `~bapsflib._hdf.utils.hdfreadcontrols.HDFReadControls` and
    :`~bapsflib._hdf.utils.hdfreaddata.HDFReadData`.

    Parameters
    ----------
    shotnum: :term:`array_like` or Union[int, slice, List[int,...]]
        Array like object of desired shot numbers.

    dset_list : List[h5py.Dataset]
        List of control dataset instances that the shot number
        ``shotnum`` should be conditioned against

    shotnumkey_list : List[str]
        A one-to-one list with ``dset_list`` that names the shot number
        column filed in the associated dataset.

    Returns
    -------
    `numpy.ndarray`
        conditioned ``shotnum`` numpy array


    .. admonition:: Condition Criteria

        #. Any :math:`\mathbf{shotnum} \le 0` will be removed.
        #. A `ValueError` will be thrown if the conditioned array is
           NULL.
    """
    # Acceptable `shotnum` types
    # 1. int
    # 2. slice() object
    # 3. List[int, ...]
    # 4. np.array (dtype = np.integer and ndim = 1)
    #
    # Catch each `shotnum` type and convert to numpy array
    #
    if isinstance(shotnum, int):
        if shotnum <= 0 or isinstance(shotnum, bool):
            raise ValueError(
                f"Valid `shotnum` ({shotnum}) not passed. Resulting array would be NULL."
            )

        # convert
        shotnum = np.array([shotnum], dtype=np.uint32)

    elif isinstance(shotnum, list):
        # ensure all elements are int
        if not all(isinstance(sn, int) for sn in shotnum):
            raise ValueError("Valid `shotnum` not passed. All values NOT int.")

        # remove shot numbers <= 0
        shotnum.sort()
        shotnum = list(set(shotnum))
        shotnum.sort()
        if min(shotnum) <= 0:
            # remove values less-than or equal to 0
            new_sn = [sn for sn in shotnum if sn > 0]
            shotnum = new_sn

        # ensure not NULL
        if len(shotnum) == 0:
            raise ValueError("Valid `shotnum` not passed. Resulting array would be NULL")

        # convert
        shotnum = np.array(shotnum, dtype=np.uint32)

    elif isinstance(shotnum, slice):
        # determine the largest possible shot number
        last_sn = [dset[-1, key] + 1 for dset, key in zip(dset_list, shotnumkey_list)]
        if shotnum.stop is not None:
            last_sn.append(shotnum.stop)
        stop_sn = max(last_sn)

        # get the start, stop, and step for the shot number array
        start, stop, step = shotnum.indices(stop_sn)

        # re-define `shotnum`
        shotnum = np.arange(start, stop, step, dtype=np.int32)

        # remove shot numbers <= 0
        shotnum = np.delete(shotnum, np.where(shotnum <= 0)[0])
        shotnum = shotnum.astype(np.uint32)

        # ensure not NULL
        if shotnum.size == 0:
            raise ValueError("Valid `shotnum` not passed. Resulting array would be NULL")

    elif isinstance(shotnum, np.ndarray):
        if shotnum.ndim != 1:
            shotnum = shotnum.squeeze()
        if (
            shotnum.ndim != 1
            or not np.issubdtype(shotnum.dtype, np.integer)
            or bool(shotnum.dtype.names)
        ):
            raise ValueError("Valid `shotnum` not passed")

        # remove shot numbers <= 0
        shotnum.sort()
        shotnum = np.delete(shotnum, np.where(shotnum <= 0)[0])
        shotnum = shotnum.astype(np.uint32)

        # ensure not NULL
        if shotnum.size == 0:
            raise ValueError("Valid `shotnum` not passed. Resulting array would be NULL")
    else:
        raise ValueError("Valid `shotnum` not passed")

    # return
    return shotnum


def do_shotnum_intersection(
    shotnum: np.ndarray, sni_dict: IndexDict, index_dict: IndexDict
) -> Tuple[np.ndarray, IndexDict, IndexDict]:
    """
    Calculates intersection of ``shotnum`` and all existing dataset
    shot numbers, ``shotnum[sni]``.

    .. admonition:: Recall Array Relationship

        .. code-block:: python

            shotnum[sni] = dset[index, shotnumkey]

    Parameters
    ----------
    shotnum : :term:`array_like`
        Array like object of desired shot numbers.

    sni_dict : `IndexDict`
        Dictionary of dictionaries of all dataset ``sni`` arrays.  The
        first level of `dict` keys is the control device name and the
        second level of `dict` keys is the desired 'state value` (e.g.
        ``'xyz'``).

    index_dict : `IndexDict`
        Dictionary of dictionaries of all dataset ``index`` arrays.  The
        first level of `dict` keys is the control device name and the
        second level of `dict` keys is the desired 'state value` (e.g.
        ``'xyz'``).

    Returns
    -------
    shotnum : `numpy.ndarray`
        intersected and re-calculated array of shot numbers

    sni_dict : `IndexDict`
        intersected and re-calculated arrays of ``sni`` indexing values
        for each dataset

    index_dict : `IndexDict`
        intersected and re-calculated arrays of ``index`` indexing
        values for each dataset
    """
    # intersect shot numbers
    shotnum_intersect = shotnum
    for control_name in sni_dict.keys():
        for state_key, sni in sni_dict[control_name].items():
            shotnum_intersect = np.intersect1d(
                shotnum_intersect, shotnum[sni], assume_unique=True
            )
    if shotnum_intersect.shape[0] == 0:
        raise ValueError("Input `shotnum` would result in a NULL array")

    # now filter
    for control_name in index_dict.keys():
        for state_key, index in index_dict[control_name].items():
            sni = sni_dict[control_name][state_key]
            mask_for_index = np.isin(shotnum[sni], shotnum_intersect)
            index_dict[control_name][state_key] = index_dict[control_name][state_key][
                mask_for_index
            ]
            sni_dict[control_name][state_key] = np.ones(
                shotnum_intersect.shape, dtype=bool
            )

    # update shotnum
    shotnum = shotnum_intersect

    # return
    return shotnum, sni_dict, index_dict
