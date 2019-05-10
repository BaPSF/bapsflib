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
Decorators associated with assisting in the usage of
:mod:`astropy.units`.
"""
__all__ = ['check_quantity', 'check_relativistic']

import astropy.units as u
import functools
import inspect
import numpy as np
import warnings

from astropy.units import UnitsWarning
from plasmapy.utils import check_relativistic
from textwrap import dedent
from typing import (Dict, List, Union)


# this is modified from plasmapy.utils.checks.check_quantity
# TODO: replace with PlasmaPy version when PlasmaPy v0.2.0 is released
def check_quantity(**validations:
                   Dict[str, Union[bool, List, None, u.Unit]]):
    """
    Verify that the function's arguments have correct units.
    This decorator raises an exception if an annotated argument in the
    decorated function is an :class:`~astropy.units.Quantity` 
    with incorrect units or of incorrect kind. You can prevent 
    arguments from being input as Nones, NaNs, negatives, 
    infinities, and complex numbers.

    If a number (non-Quantity) value is inserted in place of a value
    with units, then coerce it to the expected unit (if only one unit
    type is expected) or raise a TypeError.

    This is probably best illustrated with an example:

    Examples
    --------
    >>> from astropy import units as u
    >>> @check_quantity(x={"units": u.m,
    ...       "can_be_negative": False,
    ...       "can_be_complex": True,
    ...       "can_be_inf": True})
    ... def func(x):
    ...     return x

    >>> func(1 * u.m)
    <Quantity 1. m>

    >>> func(1 * u.s)
    Traceback (most recent call last):
      ...
    astropy.units.core.UnitConversionError: The argument x to func should be a Quantity with the following units: m

    >>> import pytest    # to show the UnitsWarning
    >>> with pytest.warns(u.UnitsWarning, match="Assuming units of m."):
    ...     func(1)
    <Quantity 1. m>

    >>> func(-1 * u.m)
    Traceback (most recent call last):
      ...
    ValueError: The argument x to function func cannot contain negative numbers.

    >>> func(np.inf * u.m)
    <Quantity inf m>

    >>> func(None)
    Traceback (most recent call last):
      ...
    ValueError: The argument x to function func cannot contain Nones.

    Parameters
    ----------
    dict
        Arguments to be validated passed in as keyword arguments,
        with values as validation dictionaries, with structure as
        in the example.  Valid keys for each argument are:
        'units': :class:`astropy.units.Unit`,
        'equivalencies': :mod:`astropy.units.equivalencies`,
        'enforce': `bool`,
        'can_be_negative': `bool`,
        'can_be_complex': `bool`,
        'can_be_inf': `bool`,
        'can_be_nan': `bool`,
        'none_shall_pass': `bool`

    Raises
    ------
    :class:`TypeError`
        If the argument is not a :class:`~astropy.units.Quantity`, 
        units is not entirely units or `argname` does not have a type
        annotation.

    :class:`~astropy.units.UnitConversionError`
        If the argument is not in acceptable units.

    :class:`~astropy.units.UnitsError`
        If after the assumption checks, the argument is still not in
        acceptable units.

    :class:`ValueError`
        If the argument contains :attr:`~numpy.nan` or other invalid 
        values as determined by the keywords.

    Warns
    -----
    :class:`~astropy.units.UnitsWarning`
        If a :class:`~astropy.units.Quantity` is not provided and 
        unique units are provided, a `UnitsWarning` will be raised 
        and the inputted units will be assumed.

    Notes
    -----
    This functionality may end up becoming deprecated due to
    noncompliance with the `IEEE 754 standard
    <https://en.wikipedia.org/wiki/IEEE_754#Exception_handling>`_
    and in favor of `~astropy.units.quantity_input`.

    Returns
    -------
    function
        Decorated function.

    See also
    --------
    :func:`_check_quantity`
    """
    def decorator(f):
        wrapped_sign = inspect.signature(f)
        fname = f.__name__

        # add '__signature__' to methods that are copied from
        # wrapped_function onto wrapper
        assigned = list(functools.WRAPPER_ASSIGNMENTS)
        assigned.append('__signature__')
        @functools.wraps(f, assigned=assigned)
        def wrapper(*args, **kwargs):
            # combine args and kwargs into dictionary
            bound_args = wrapped_sign.bind(*args, **kwargs)
            bound_args.apply_defaults()
            given_params_values = bound_args.arguments
            given_params = set(given_params_values.keys())

            # names of params to check
            validated_params = set(validations.keys())

            missing_params = [
                param for param in (validated_params - given_params)
            ]

            if len(missing_params) > 0:
                params_str = ", ".join(missing_params)
                raise TypeError(
                    f"Call to {fname} is missing "
                    f"validated params {params_str}")

            for param_to_check, validation_settings \
                    in validations.items():
                value_to_check = given_params_values[param_to_check]

                equivalencies = \
                    validation_settings.get('equivalencies', None)
                can_be_negative = \
                    validation_settings.get('can_be_negative', True)
                can_be_complex = \
                    validation_settings.get('can_be_complex', False)
                can_be_inf = \
                    validation_settings.get('can_be_inf', True)
                can_be_nan = \
                    validation_settings.get('can_be_nan', True)
                none_shall_pass = \
                    validation_settings.get('none_shall_pass', False)

                validated_value = _check_quantity(
                    value_to_check,
                    param_to_check,
                    fname,
                    validation_settings['units'],
                    equivalencies=equivalencies,
                    can_be_negative=can_be_negative,
                    can_be_complex=can_be_complex,
                    can_be_inf=can_be_inf,
                    can_be_nan=can_be_nan,
                    none_shall_pass=none_shall_pass,
                )
                given_params_values[param_to_check] = validated_value

            return f(**given_params_values)

        # add '__signature__' if it does not exist
        # - this will preserve parameter hints in IDE's
        if not hasattr(wrapper, '__signature__'):
            wrapper.__signature__ = inspect.signature(f)

        return wrapper
    return decorator


# this is modified from plasmapy.utils.checks._check_quantity
# TODO: replace with PlasmaPy version when PlasmaPy v0.2.0 is released
def _check_quantity(val: u.Quantity,
                    val_name: str,
                    funcname: str,
                    units: u.UnitBase,
                    equivalencies: Union[List, None] = None,
                    enforce: bool = True,
                    can_be_negative: bool = True,
                    can_be_complex: bool = False,
                    can_be_inf: bool = True,
                    can_be_nan: bool = True,
                    none_shall_pass: bool = False):
    """
    To be used with decorator :func:`check_quantity`.

    Raise an exception if an object is not a
    :class:`~astropy.units.Quantity` with correct units and
    valid numerical values.

    Parameters
    ----------
    val : :class:`~astropy.units.Quantity`
        The object to be tested.

    val_name: str
        The name of the variable passed in as :data:`val`.
        (used for error messages)

    funcname : str
        The name of the decorated function. (used for error messages)

    equivalencies : Union[None, List[Tuple]]
        An :mod:`astropy.units.equivalencies` used to help with
        unit conversion.

    enforce : bool
        (:code:`True` DEFAULT) Force the input :data:`val` to be
        converted into the desired :data:`units`

    units : :class:`~astropy.units.Unit` or list of :class:`~astropy.unit.Unit`
        Acceptable units for :data:`val`.

    can_be_negative : bool, optional
        `True` if the `~astropy.units.Quantity` can be negative,
        `False` otherwise.  Defaults to `True`.

    can_be_complex : bool, optional
        `True` if the `~astropy.units.Quantity` can be a complex number,
        `False` otherwise.  Defaults to `False`.

    can_be_inf : bool, optional
        `True` if the `~astropy.units.Quantity` can contain infinite
        values, `False` otherwise.  Defaults to `True`.

    can_be_nan : bool, optional
        `True` if the `~astropy.units.Quantity` can contain NaN
        values, `False` otherwise.  Defaults to `True`.

    none_shall_pass : bool, optional
        `True` if the `~astropy.units.Quantity` can contain None
        values, `False` otherwise.  Defaults to `True`.

    Raises
    ------
    TypeError
        If the argument is not a `~astropy.units.Quantity` or units is
        not entirely units.

    ~astropy.units.UnitConversionError
        If the argument is not in acceptable units.

    ~astropy.units.UnitsError
        If after the assumption checks, the argument is still not in
        acceptable units.

    ValueError
        If the argument contains any `~numpy.nan` or other invalid
        values as determined by the keywords.

    Warns
    -----
    ~astropy.units.UnitsWarning
        If a `~astropy.units.Quantity` is not provided and unique units
        are provided, a `UnitsWarning` will be raised and the inputted
        units will be assumed.

    Examples
    --------
    >>> from astropy import units as u
    >>> import pytest
    >>> _check_quantity(4*u.T, 'B', 'f', u.T)
    <Quantity 4. T>
    >>> with pytest.warns(u.UnitsWarning, match="No units are specified"):
    ...     assert _check_quantity(4, 'B', 'f', u.T) == 4 * u.T
    """
    # -- condition `units` argument --
    if not isinstance(units, list):
        units = [units]
    for unit in units:
        if not isinstance(unit,
                          (u.Unit, u.CompositeUnit, u.IrreducibleUnit)):
            raise TypeError(
                "The `units` arg must be a list of astropy units."
            )

    # -- condition `equivalencies` keyword --
    if equivalencies is None:
        equivalencies = [None] * len(units)
    elif isinstance(equivalencies, list):
        if all(isinstance(el, tuple) for el in equivalencies):
            equivalencies = [equivalencies]

        # ensure passed equivalencies list is structured properly
        #   [[(), ...], ...]
        for equivs in equivalencies:
            for equiv in equivs:
                err_str = (
                    "All equivalencies must be a list of 4 element "
                    "tuples structured like (unit1, unit2, "
                    "func_unit1_to_unit2, func_unit2_to_unit1)"
                )
                if not isinstance(equiv, tuple):
                    raise TypeError(err_str)
                elif len(equiv) != 4:
                    raise TypeError(err_str)

        # ensure number of equivalencies lists match the number of
        # equivalent units to check
        if len(equivalencies) == 1:
            equivalencies = equivalencies * len(units)
        elif len(equivalencies) != len(units):
            raise ValueError(
                f"The length of the specified equivalencies list "
                f"({len(equivalencies)}) must be 1 or equal to the "
                f"number of specified units ({len(units)})")

    # -- condition `val` argument --
    # create a TypeError message
    typeerror_message = (
        f"The argument {val_name} to {funcname} should be a "
        f"Quantity with "
    )
    if len(units) == 1:
        typeerror_message += f"the following units: {str(units[0])}"
    else:
        typeerror_message += "one of the following units: "
        for unit in units:
            typeerror_message += str(unit)
            if unit != units[-1]:
                typeerror_message += ", "
    if none_shall_pass:
        typeerror_message += "or None "

    # initialize a ValueError meassage
    valueerror_message = (
        f"The argument {val_name} to function {funcname} can "
        f"not contain"
    )

    # ensure `val` is astropy.units.Quantity or return None (if allowed)
    if val is None and none_shall_pass:
        return val
    elif val is None:
        raise ValueError(f"{valueerror_message} Nones.")
    elif not isinstance(val, u.Quantity):
        if len(units) != 1:
            raise TypeError(typeerror_message)
        else:
            try:
                val = val * units[0]
            except (ValueError, TypeError):
                raise TypeError(typeerror_message)
            else:
                if not isinstance(val, u.Quantity):  # pragma: no cover
                    # this should never be reached...if so, except
                    # is not setup correctly
                    #
                    raise TypeError(typeerror_message)

                warnings.warn(UnitsWarning(
                    f"No units are specified for {val_name} = {val} "
                    f"in {funcname}. Assuming units of "
                    f"{str(units[0])}. To silence this warning, "
                    f"explicitly pass in an Astropy Quantity "
                    f"(e.g. 5. * astropy.units.cm) "
                    f"(see http://docs.astropy.org/en/stable/units/)"
                ))

    # Look for unit equivalencies for `val`
    in_acceptable_units = []
    for unit, equiv in zip(units, equivalencies):
        try:
            val.unit.to(unit, equivalencies=equiv)
        except u.UnitConversionError:
            in_acceptable_units.append(False)
        else:
            in_acceptable_units.append(True)

    # convert `val` to desired units if enforce=True
    nacceptable = np.count_nonzero(in_acceptable_units)
    if nacceptable == 0:
        # NO equivalent units
        raise u.UnitConversionError(typeerror_message)
    elif nacceptable == 1 and enforce:
        # convert to desired unit
        unit = np.array(units)[in_acceptable_units][0]
        equiv = np.array(equivalencies)[in_acceptable_units][0]
        val = val.to(unit, equivalencies=equiv)
    elif nacceptable >= 1 and enforce:
        # too many equivalent units
        raise u.UnitConversionError(
            "`val`'s units is equivalent to too many units in "
            "`units`, `val` can not be coerced into one")

    # ensure `val` has valid numerical values
    if np.any(np.isnan(val.value)) and not can_be_nan:
        raise ValueError(f"{valueerror_message} NaNs.")
    elif np.any(np.iscomplex(val.value)) and not can_be_complex:
        raise ValueError(f"{valueerror_message} complex numbers.")
    elif not can_be_negative:
        # Allow NaNs through without raising a warning
        with np.errstate(invalid='ignore'):
            isneg = np.any(val.value < 0)
        if isneg:
            raise ValueError(f"{valueerror_message} negative numbers.")
    elif not can_be_inf and np.any(np.isinf(val.value)):
        raise ValueError(f"{valueerror_message} infs.")

    return val
