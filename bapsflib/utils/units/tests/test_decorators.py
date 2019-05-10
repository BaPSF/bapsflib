# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2019 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
import astropy.units as u
import inspect
import numpy as np
import unittest as ut

from ..decorators import (_check_quantity, check_quantity)


class TestCheckQuantity(ut.TestCase):
    """
    Test case for function :func:`_check_quantity` and decorator
    :func:`check_quantity`
    """
    # What to cover:
    # 1. Errors raised
    #       * TypeError if all elements of the `units` arg is
    #         not and instance of u.Unit, u.CompositeUnit, or
    #         u.IrreducibleUnit
    #       * TypeError if equivalencies element is not a tuple
    #       * TypeError if equivalencies element is a tuple, but
    #         not length 4
    #       * ValueError if len(equivalencies) != 1 and != len(units)
    #       * ValueError if val is None and none_shall_pass=False
    #       * ValueError if len(units) != 1 and `val` is not u.Quantity
    #       * TypeError if len(units) == 1 and `val` is not u.Quantity
    #         and `val` can not be cast into a u.Quantity
    #       * u.UnitConversionError if no unit equivalencies are found
    #       * u.UnitConversionError if multiple equivalences are found
    #         and enforce=True
    #       * ValueError if val is np.nan and can_be_nan=False
    #       * ValueError if val is complex and can_be_complex=False
    #       * ValueError if val is negative and can_be_negative=False
    #       * ValueError if val is inf and can_be_inf=False
    # 2. UserWarnings
    #       * if len(units) == 1 and `val` is not u.Quantity and
    #         `val` can be cast into a u.Quantity
    #

    def setUp(self) -> None:
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()

    def test__check_quantity_default(self):
        """Test default values :func:`_check_quantity`."""
        sig = inspect.signature(_check_quantity)

        # _check_quantity is a function
        self.assertTrue(inspect.isfunction(_check_quantity))

        # check defaults for keywords
        pairs = [
            ('equivalencies', None),
            ('enforce', True),
            ('can_be_negative', True),
            ('can_be_complex', False),
            ('can_be_inf', True),
            ('can_be_nan', True),
            ('none_shall_pass', False),
        ]
        for pair in pairs:
            self.assertIn(pair[0], sig.parameters.keys())
            if pair[0] is None:
                self.assertIsNone(sig.parameters[pair[0]].default)
            else:
                self.assertEqual(sig.parameters[pair[0]].default,
                                 pair[1])

    def test__check_quantity_errors(self):
        """
        Test scenarios the cause :func:`_check_quantity` to raise
        errors.
        """
        # Errors to check:
        # X 1.  TypeError if all elements of the `units` arg is
        #       not and instance of u.Unit, u.CompositeUnit, or
        #       u.IrreducibleUnit
        # X 2.  TypeError if equivalencies element is not a tuple
        # X 3.  TypeError if equivalencies element is a tuple, but
        #       not length 4
        # X 4.  ValueError if len(equivalencies) != 1 and != len(units)
        # X 5.  ValueError if val is None and none_shall_pass=False
        # X 6.  TypeError if len(units) != 1 and `val` is not
        #       u.Quantity
        # X 7.  TypeError if len(units) == 1 and `val` is not u.Quantity
        #       and `val` can not be cast into a u.Quantity
        # X 8.  u.UnitConversionError if no unit equivalencies are found
        # X 9.  u.UnitConversionError if multiple equivalences are found
        #       and enforce=True
        # X 10. ValueError if val is np.nan and can_be_nan=False
        # X 11. ValueError if val is complex and can_be_complex=False
        # X 12. ValueError if val is negative and can_be_negative=False
        # X 13. ValueError if val is inf and can_be_inf=False
        #   14. ValueError if equivalencies is not a list or None
        #
        # TypeError if all elements of the `units` arg is            (1)
        # not and instance of u.Unit, u.CompositeUnit, or
        # u.IrreducibleUnit
        self.assertRaises(TypeError, _check_quantity,
                          5. * u.cm, 'a', 'foo', 'not a unit')
        self.assertRaises(TypeError, _check_quantity,
                          5. * u.cm, 'a', 'foo', [u.cm, 'not a unit'])

        # TypeError if equivalencies element is not a tuple          (2)
        self.assertRaises(TypeError, _check_quantity,
                          5. * u.cm, 'a', 'foo', u.cm,
                          equivalencies=[{'not a tuple': 1}])

        # TypeError if equivalencies element is a tuple, but         (3)
        # not length 4
        self.assertRaises(TypeError, _check_quantity,
                          5. * u.cm, 'a', 'foo', u.cm,
                          equivalencies=[(1, 2, 3, )])

        # ValueError if len(equivalencies) != 1 and != len(units)    (4)
        self.assertRaises(ValueError, _check_quantity,
                          5. * u.cm, 'a', 'foo', [u.cm, u.g, u.s],
                          equivalencies=[[(None, None, None, None)],
                                         [(None, None, None, None)]])

        # ValueError if val is None and none_shall_pass=False        (5)
        self.assertRaises(ValueError, _check_quantity,
                          None, 'a', 'foo', u.cm, none_shall_pass=False)

        # TypeError if len(units) != 1 and `val` is not              (6)
        # u.Quantity
        self.assertRaises(TypeError, _check_quantity,
                          5., 'a', 'foo', [u.cm, u.g])

        # TypeError if len(units) == 1 and `val` is not              (7)
        # u.Quantity and `val` can not be cast into a u.Quantity
        #
        # 'five' * u.cm raise a ValueError caught by try-except
        self.assertRaises(TypeError, _check_quantity,
                          'five', 'a', 'foo', u.cm)
        # {'five': 5} * u.cm raise a TypeError caught by try-except
        self.assertRaises(TypeError, _check_quantity,
                          {'five': 5}, 'a', 'foo', u.cm)

        # u.UnitConversionError if no unit equivalencies are found   (8)
        self.assertRaises(u.UnitConversionError, _check_quantity,
                          5. * u.cm, 'a', 'foo', u.g)
        self.assertRaises(u.UnitConversionError, _check_quantity,
                          5. * u.cm, 'a', 'foo', [u.g, u.s])

        # u.UnitConversionError if multiple equivalences are         (9)
        # found and enforce=True
        self.assertRaises(u.UnitConversionError, _check_quantity,
                          5. * u.cm, 'a', 'foo', [u.cm, u.km, u.g],
                          enforce=True)

        # ValueError if val is np.nan and can_be_nan=False          (10)
        self.assertRaises(ValueError, _check_quantity,
                          np.nan * u.cm, 'a', 'foo', u.cm,
                          can_be_nan=False)

        # ValueError if val is complex and can_be_complex=False     (11)
        self.assertRaises(ValueError, _check_quantity,
                          np.complex(5.) * u.cm, 'a', 'foo', u.cm,
                          can_be_complex=False)

        # ValueError if val is negative and can_be_negative=False   (12)
        self.assertRaises(ValueError, _check_quantity,
                          -5. * u.g, 'a', 'foo', u.g,
                          can_be_negative=False)

        # ValueError if val is inf and can_be_inf = False           (13)
        self.assertRaises(ValueError, _check_quantity,
                          np.inf * u.cm, 'a', 'foo', u.cm,
                          can_be_inf=False)

        # ValueError if equivalencies is not a list or None         (14)
        self.assertRaises(ValueError, _check_quantity,
                          np.inf * u.cm, 'a', 'foo', u.cm,
                          equivalencies=('not', 'correct'))

    def test__check_quantity_behavior(self):
        """Test behavior of :func:`_check_quantity` keywords."""
        # -- keyword `can_be_complex` --
        vals = [np.complex(5., 2.) * u.cm,
                np.array([1, 4, 6], dtype=np.complex) * u.cm]
        for val in vals:
            check_val = _check_quantity(val, 'val', 'foo', u.m,
                                        can_be_complex=True)
            self.assertTrue(
                np.all((val.value / 100.0) * u.m == check_val))
            self.assertTrue(np.all(np.iscomplexobj(check_val.value)))

        # -- keyword `can_be_inf` --
        vals = [np.inf * u.cm,
                np.array([1, np.inf, 6], dtype=np.float16) * u.cm]
        for val in vals:
            check_val = _check_quantity(val, 'val', 'foo', u.m,
                                        can_be_inf=True)
            self.assertTrue(
                np.all((val.value / 100.0) * u.m == check_val))
            self.assertEqual(np.count_nonzero(np.isinf(val)),
                             np.count_nonzero(np.isinf(check_val)))

        # -- keyword `can_be_nan` --
        vals = [np.nan * u.cm,
                np.array([1, np.nan, 6], dtype=np.float16) * u.cm]
        for val in vals:
            check_val = _check_quantity(val, 'val', 'foo', u.m,
                                        can_be_nan=True)
            self.assertEqual(u.m, check_val.unit)
            if isinstance(val, np.ndarray) and val.size != 1:
                val_mask = np.isnan(val)
                check_val_mask = np.isnan(check_val)
                self.assertEqual(np.count_nonzero(val_mask),
                                 np.count_nonzero(check_val_mask))
                self.assertTrue(np.array_equal(
                    val[np.logical_not(val_mask)] / 100.0,
                    check_val[np.logical_not(check_val_mask)]
                ))
            else:
                self.assertTrue(np.isnan(check_val))

        # -- keyword `can_be_negative` --
        vals = [-5. * u.cm,
                np.array([-1., 3., -22.], dtype=np.float16) * u.cm]
        for val in vals:
            check_val = _check_quantity(
                val, 'val', 'foo', u.m, can_be_negative=True)
            self.assertTrue(np.array_equal(
                (val.value / 100.0) * u.m,
                check_val))

        # val is positive and negative are not allowed
        val = 5.0 * u.cm
        check_val = _check_quantity(
            val, 'val', 'foo', u.m, can_be_negative=False)
        self.assertEqual((val.value / 100.0) * u.m, check_val)

        # -- keyword `enforce` --
        vals = [5. * u.cm,
                np.array([1., 3., 22.], dtype=np.float16) * u.cm]
        for val in vals:
            check_val = _check_quantity(
                val, 'val', 'foo', u.cm, enforce=True)
            self.assertTrue(np.array_equal(val, check_val))

            check_val = _check_quantity(
                val, 'val', 'foo', u.km, enforce=True)
            self.assertTrue(np.array_equal(val.to(u.km), check_val))

            check_val = _check_quantity(
                val, 'val', 'foo', u.km, enforce=False)
            self.assertTrue(np.array_equal(val, check_val))

        # -- keyword `equivalencies` --
        # equivalencies is one list but multiple units are specific
        val = 5. * u.K
        check_val = _check_quantity(
            val, 'val', 'foo', [u.cm, u.deg_C],
            equivalencies=u.temperature())
        self.assertEqual(
            val.to(u.deg_C, equivalencies=u.temperature()), check_val)

        # number of equivalencies and units are equal but more that 1
        check_val = _check_quantity(
            val, 'val', 'foo', [u.deg_C, u.g],
            equivalencies=[u.temperature(), u.molar_mass_amu()])
        self.assertEqual(
            val.to(u.deg_C, equivalencies=u.temperature()), check_val)

        # -- keyword `non_shall_pass` --
        val = None
        check_val = _check_quantity(
            val, 'val', 'foo', u.cm, none_shall_pass=True)
        self.assertIsNone(check_val)

    def test__check_quantity_warnings(self):
        """
        Test behavior that cause :func:`_check_quantity` to issue
        a UserWarning
        """
        # value does not have units and only one unit is specified
        val = 5
        with self.assertWarns(u.UnitsWarning):
            check_val = _check_quantity(val, 'val', 'foo', u.cm)
            self.assertEqual(val * u.cm, check_val)


if __name__ == '__main__':
    ut.main()
