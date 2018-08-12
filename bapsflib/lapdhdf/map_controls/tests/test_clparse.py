#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
from ..clparse import CLParse

import unittest as ut

import re


class TestCLParse(ut.TestCase):
    """Test class for CLParse"""
    # `try_patterns` method just prints results of `apply_patters` so
    # not testing the method
    #
    def test_attributes(self):
        """Test fore basic attributes of object."""
        clparse = CLParse(['one', 'two'])
        self.assertTrue(hasattr(clparse, '_cl'))
        self.assertTrue(hasattr(clparse, 'apply_patterns'))
        self.assertTrue(hasattr(clparse, 'try_patterns'))

    def test_apply_patterns(self):
        """
        Test functionality of
        :meth:`bapsflib.lapdhdf.map_controls.clparse.CLParse.apply_patterns`
        """
        # What to test:
        # 1. output is always a (bool, dict)
        # 2. inputs
        #    - Raise ValueError for
        #      * not a string or list
        #      * list of no strings
        #      * list of strings and not strings
        # 3. defining symbolic groups
        #    - every pattern must define 2 symbolic groups, one of which
        #      has to be 'VAL'
        #    - Raise ValueError for
        #      * 2 symbolic groups are NOT defined
        #      * 2 symbolic groups are defined, but 'VAL' not one
        # 4. pattern is successful and,
        #    - NO remainder of command string
        #    - STILL remainder of command string
        # 5. pattern is not successful, returned dict is None
        #
        # initialize CLParse
        cl = ['FREQ 50.0', 'FREQ 60.0', 'FREQ 70.0']
        clparse = CLParse(cl)

        # ------ Inputs that should raise ValueError              ------
        inputs = [
            5,
            [2, 3, 4],
            ['one', 2]
        ]
        for patterns in inputs:
            self.assertRaises(ValueError,
                              clparse.apply_patterns, patterns)

        # --- Patterns that don't properly define symbolic groups ------
        # - does not define symbolic groups 'VAL' and <NAME>
        # - ONLY defines symbolic group 'VAL'
        # - ONLY defines symbolic group <NAME>
        # - Defines symbolic group <NAME> multiple times w/ differing
        #   patterns
        #
        # <NAME> is the name of probe state value, e.g. <NAME> = 'FREQ'
        inputs = [
            r'(\bVOLT\s)',
            r'((\bFREQ\s)((\d+\.\d*|\.\d+|\d+\b)))',
            r'(?P<FREQ>(\bFREQ\s)((\d+\.\d*|\.\d+|\d+\b)))',
            r'((\bFREQ\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))',
            r'(?P<FREQ>(\bFREQ\s)(?P<value>(\d+\.\d*|\.\d+|\d+\b)))',
            [r'(?P<FREQ>(\bFREQ\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))',
             r'(?P<FREQ>(\bFREQ\s)(?P<VAL>(\w+\.\d*|\.\d+|\d+\b)))']
        ]
        for patterns in inputs:
            self.assertRaises(ValueError,
                              clparse.apply_patterns, patterns)

        # --- Patterns that cause warnings                        ------
        # - generated command list has None values
        # - generated command list is not all same type
        # - generated command list is all null strings
        #
        # Generated command list has None values
        pattern = r'(?P<VOLT>(\bVOLT\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))'
        self.assertWarns(UserWarning, clparse.apply_patterns, pattern)
        self.assertApplyPatternOutput(clparse.apply_patterns(pattern))

        # Generated command list is not all same type
        cl = ['FREQ 50.0', 'FREQ A.0', 'FREQ 70.0']
        clparse = CLParse(cl)
        pattern = r'(?P<FREQ>(\bFREQ\s)(?P<VAL>(\w+\.\d*|\.\d+|\d+\b)))'
        self.assertWarns(UserWarning, clparse.apply_patterns, pattern)
        self.assertApplyPatternOutput(clparse.apply_patterns(pattern))

        # Generated command list is all null strings
        cl = ['FREQ 50.0', 'FREQ 60.0', 'FREQ 70.0']
        clparse = CLParse(cl)
        pattern = r'(?P<FREQ>(\bFREQ\s)(?P<VAL>))'
        self.assertWarns(UserWarning, clparse.apply_patterns, pattern)
        self.assertApplyPatternOutput(clparse.apply_patterns(pattern))

        # --- Valid Patterns, but Unsuccessful                    ------
        # - i.e. pattern meets input criteria, but has no match in the
        #   command list and the resulting dict would only have the
        #   'remainder' key
        cl = ['FREQ 50.0', 'FREQ 60.0', 'FREQ 70.0']
        clparse = CLParse(cl)
        pattern = r'(?P<VOLT>(\bVOLT\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))'
        self.assertApplyPatternOutput(clparse.apply_patterns(pattern))

        # --- Valid Patterns and Successful                       ------
        # - single pattern and no remainder
        # - single pattern and remainder
        # - two patterns and no remainder
        #
        # Single pattern and no remainder
        cl = ['FREQ 50.0', 'FREQ 60.0', 'FREQ 70.0']
        clparse = CLParse(cl)
        pattern = r'(?P<FREQ>(\bFREQ\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))'
        output = clparse.apply_patterns(pattern)
        self.assertApplyPatternOutput(output)
        self.assertEqual(output[1]['FREQ']['command list'],
                         (50.0, 60.0, 70.0))

        # Single pattern and remainder
        cl = ['FREQ 50.0 VOLT 20',
              'FREQ 60.0 VOLT 25.0',
              'FREQ 70.0 VOLT 30']
        clparse = CLParse(cl)
        pattern = r'(?P<FREQ>(\bFREQ\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))'
        output = clparse.apply_patterns(pattern)
        self.assertApplyPatternOutput(output)
        self.assertEqual(output[1]['FREQ']['command list'],
                         (50.0, 60.0, 70.0))
        self.assertEqual(output[1]['remainder']['command list'],
                         ('VOLT 20', 'VOLT 25.0', 'VOLT 30'))

        # Two patterns and no remainder
        cl = ['FREQ 50.0 VOLT 20',
              'FREQ 60.0 VOLT 25.0',
              'FREQ 70.0 VOLT 30']
        clparse = CLParse(cl)
        pattern = [
            r'(?P<FREQ>(\bFREQ\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))',
            r'(?P<VOLT>(\bVOLT\s)(?P<VAL>(\d+\.\d*|\.\d+|\d+\b)))'
        ]
        output = clparse.apply_patterns(pattern)
        self.assertApplyPatternOutput(output)
        self.assertEqual(output[1]['FREQ']['command list'],
                         (50.0, 60.0, 70.0))
        self.assertEqual(output[1]['VOLT']['command list'],
                         (20.0, 25.0, 30.0))

    def assertApplyPatternOutput(self, output: Tuple[bool, dict]):
        # output[0] - success of applying patterns
        # output[1] - state values dictionary
        #
        self.assertIsInstance(output, tuple)
        self.assertEqual(len(output), 2)
        self.assertIsInstance(output[0], bool)
        if output[0]:
            # should be a dict
            self.assertIsInstance(output[1], dict)

            # if dict is len 1, then 'remainder' should NOT be the key
            if len(output[1].keys()) == 1:
                self.assertNotIn('remainder', output[1])

            # check for required fields
            for name in output[1]:
                self.assertIn('re pattern', output[1][name])
                self.assertIn('command list', output[1][name])
                self.assertIn('cl str', output[1][name])

                # check types
                if name == 'remainder':
                    self.assertIsNone(output[1][name]['re pattern'])
                else:
                    self.assertIsInstance(output[1][name]['re pattern'],
                                          type(re.compile(r'')))
                self.assertIsInstance(output[1][name]['command list'],
                                      tuple)
                self.assertIsInstance(output[1][name]['cl str'],
                                      tuple)

                # check 'command list'
                self.assertTrue(all(
                    isinstance(command,
                               type(output[1][name]['command list'][0]))
                    for command in output[1][name]['command list']))
                self.assertEqual(len(output[1][name]['command list']),
                                 len(output[1][name]['cl str']))

                # check 'cl str'
                self.assertTrue(all(
                    isinstance(command, str)
                    for command in output[1][name]['cl str']))
        else:
            self.assertIsNone(output[1])


if __name__ == '__main__':
    ut.main()
