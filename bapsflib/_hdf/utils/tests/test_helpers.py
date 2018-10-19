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
import unittest as ut

from . import TestBase
from ..file import File
from ..helpers import condition_controls


class TestConditionControls(TestBase):
    """Test Case for condition_controls"""
    # What to test:
    # 1. passing of non lapd.File object
    #    - raises AttributeError
    # 2. passing of controls as None (or not a list)
    #    - raises TypeError
    # 3. HDF5 file with no controls
    #    - raises AttributeError
    # 4. HDF5 file with one control
    #    - pass controls with
    #      a. just control name, no config
    #      b. control name and valid config
    #      c. control name and invalid config
    #      d. two control names
    # 5. HDF5 file with multiple controls
    #

    def setUp(self):
        # setup HDF5 file
        super().setUp()

    def tearDown(self):
        super().tearDown()

    @property
    def lapdf(self):
        return File(self.f.filename)

    def test_input_failures(self):
        """Test input failures of `controls`"""
        # `controls` is Null
        self.assertRaises(ValueError,
                          condition_controls, self.lapdf, [])

        # `controls` is not a string or Iterable
        self.assertRaises(TypeError,
                          condition_controls, self.lapdf, True)

        # 'controls` element is not a str or tuple
        self.assertRaises(TypeError,
                          condition_controls,
                          self.lapdf, ['Waveform', 8])

        # `controls` tuple element has length > 2
        self.assertRaises(ValueError,
                          condition_controls,
                          self.lapdf, [('Waveform', 'c1', 'c2')])

    def test_file_w_one_control(self):
        """
        Test `controls` conditioning for file with one control device.
        """
        # set one control device
        self.f.add_module('Waveform',
                          mod_args={'n_configs': 1, 'sn_size': 100})
        _lapdf = self.lapdf

        # ---- Waveform w/ one Configuration                        ----
        # conditions that work
        con_list = [
            'Waveform',
            ('Waveform', ),
            ['Waveform'],
            [('Waveform', 'config01')],
        ]
        for og_con in con_list:
            self.assertEqual(
                condition_controls(_lapdf, og_con),
                [('Waveform', 'config01')])

        # conditions that raise ValueError
        con_list = [
            ['Waveform', 'config01'],
            ['Waveform', ('Waveform', 'config01')],
            ['Waveform', '6K Compumotor'],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf, og_con)

        # ---- Waveform w/ three Configurations                     ----
        self.f.modules['Waveform'].knobs.n_configs = 3
        _lapdf = self.lapdf

        # conditions that work
        con_list = [
            [('Waveform', 'config01')],
            [('Waveform', 'config02')]
        ]
        for og_con in con_list:
            self.assertEqual(
                condition_controls(_lapdf, og_con),
                og_con)

        # conditions that raise ValueError
        con_list = [
            ['Waveform'],
            ['6K Compumotor', ('Waveform', 'config01')],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf,
                              og_con)

    def test_file_w_multiple_controls(self):
        """
        Test `controls` conditioning for file with multiple (2) control
        devices.
        """
        # set modules
        self.f.add_module('Waveform',
                          {'n_configs': 1, 'sn_size': 100})
        self.f.add_module('6K Compumotor',
                          {'n_configs': 1, 'sn_size': 100})

        # ---- 1 Waveform Config & 1 6K Config                      ----
        _lapdf = self.lapdf
        sixk_cspec = self.f.modules['6K Compumotor'].config_names[0]

        # conditions that work
        con_list = [
            ('Waveform',
             [('Waveform', 'config01')]),
            (['Waveform'],
             [('Waveform', 'config01')]),
            ([('Waveform', 'config01')],
             [('Waveform', 'config01')]),
            (['6K Compumotor'],
             [('6K Compumotor', sixk_cspec)]),
            ([('6K Compumotor', sixk_cspec)],
             [('6K Compumotor', sixk_cspec)]),
            (['Waveform', '6K Compumotor'],
             [('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)]),
            (['Waveform', ('6K Compumotor', sixk_cspec)],
             [('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)]),
            ([('Waveform', 'config01'), '6K Compumotor'],
             [('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)]),
            ([('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)],
             [('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)]),
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(condition_controls(_lapdf, og_con),
                             correct_con)

        # conditions that raise TypeError
        con_list = [
            ['6K Compumotor', sixk_cspec],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError,
                              condition_controls, _lapdf, og_con)

        # conditions that raise ValueError
        con_list = [
            ['Waveform', 'config01'],
            ['Waveform', ('Waveform', 'config01')],
            ['6K Compumotor', ('6K Compumotor', sixk_cspec)],
            [('Waveform', 'config02')],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf, og_con)

        # ---- 3 Waveform Config & 1 6K Config                      ----
        self.f.modules['Waveform'].knobs.n_configs = 3
        _lapdf = self.lapdf
        sixk_cspec = self.f.modules['6K Compumotor'].config_names[0]

        # conditions that work
        con_list = [
            ([('Waveform', 'config01')],
             [('Waveform', 'config01')]),
            ([('Waveform', 'config03')],
             [('Waveform', 'config03')]),
            ('6K Compumotor',
             [('6K Compumotor', sixk_cspec)]),
            (['6K Compumotor'],
             [('6K Compumotor', sixk_cspec)]),
            ([('6K Compumotor', sixk_cspec)],
             [('6K Compumotor', sixk_cspec)]),
            ([('Waveform', 'config01'), '6K Compumotor'],
             [('Waveform', 'config01'), ('6K Compumotor', sixk_cspec)]),
            ([('Waveform', 'config02'), ('6K Compumotor', sixk_cspec)],
             [('Waveform', 'config02'), ('6K Compumotor', sixk_cspec)]),
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(
                condition_controls(_lapdf, og_con),
                correct_con)

        # conditions that raise TypeError
        con_list = [
            ['6K Compumotor', sixk_cspec],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError,
                              condition_controls, _lapdf, og_con)

        # conditions that raise ValueError
        con_list = [
            ['Waveform'],
            ['Waveform', 'config01'],
            ['Waveform', '6K Compumotor'],
            ['Waveform', ('6K Compumotor', sixk_cspec)],
            ['Waveform', ('Waveform', 'config01')],
            ['6K Compumotor', ('6K Compumotor', sixk_cspec)],
            [('Waveform', 'config05')],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf, og_con)

        # ---- 1 Waveform Config & 3 6K Config                      ----
        self.f.modules['Waveform'].knobs.n_configs = 1
        self.f.modules['6K Compumotor'].knobs.n_configs = 3
        _lapdf = self.lapdf
        sixk_cspec = self.f.modules['6K Compumotor'].config_names

        # conditions that work
        con_list = [
            (['Waveform'],
             [('Waveform', 'config01')]),
            ([('Waveform', 'config01')],
             [('Waveform', 'config01')]),
            ([('6K Compumotor', sixk_cspec[0])],
             [('6K Compumotor', sixk_cspec[0])]),
            ([('6K Compumotor', sixk_cspec[2])],
             [('6K Compumotor', sixk_cspec[2])]),
            (['Waveform', ('6K Compumotor', sixk_cspec[1])],
             [('Waveform', 'config01'),
              ('6K Compumotor', sixk_cspec[1])])
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(condition_controls(_lapdf, og_con),
                             correct_con)

        # conditions that raise TypeError
        con_list = [
            ['6K Compumotor', sixk_cspec[0]],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError,
                              condition_controls, _lapdf, og_con)

        # conditions that raise ValueError
        con_list = [
            ['Waveform', 'config01'],
            ['6K Compumotor'],
            ['Waveform', '6K Compumotor'],
            [('Waveform', 'config01'), '6K Compumotor'],
            ['Waveform', ('Waveform', 'config01')],
            ['6K Compumotor', ('6K Compumotor', sixk_cspec[1])],
            [('Waveform', 'config02')],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf, og_con)

        # ---- 3 Waveform Config & 3 6K Config                      ----
        self.f.modules['Waveform'].knobs.n_configs = 3
        _lapdf = self.lapdf
        sixk_cspec = self.f.modules['6K Compumotor'].config_names

        # conditions that work
        con_list = [
            ([('Waveform', 'config01')],
             [('Waveform', 'config01')]),
            ([('Waveform', 'config02')],
             [('Waveform', 'config02')]),
            ([('6K Compumotor', sixk_cspec[0])],
             [('6K Compumotor', sixk_cspec[0])]),
            ([('6K Compumotor', sixk_cspec[2])],
             [('6K Compumotor', sixk_cspec[2])]),
            ([('Waveform', 'config03'),
              ('6K Compumotor', sixk_cspec[1])],
             [('Waveform', 'config03'),
              ('6K Compumotor', sixk_cspec[1])])
        ]
        for og_con, correct_con in con_list:
            self.assertEqual(condition_controls(_lapdf, og_con),
                             correct_con)

        # conditions that raise TypeError
        con_list = [
            ['6K Compumotor', sixk_cspec[0]],
        ]
        for og_con in con_list:
            self.assertRaises(TypeError,
                              condition_controls, _lapdf, og_con)

        # conditions that raise ValueError
        con_list = [
            ['Waveform'],
            ['Waveform', 'config01'],
            ['6K Compumotor'],
            ['Waveform', '6K Compumotor'],
            [('Waveform', 'config01'), '6K Compumotor'],
            ['Waveform', ('Waveform', 'config01')],
            ['6K Compumotor', ('6K Compumotor', sixk_cspec[1])],
        ]
        for og_con in con_list:
            self.assertRaises(ValueError,
                              condition_controls, _lapdf,
                              og_con)

    def test_controls_w_same_contype(self):
        """
        Test `controls` conditioning for multiple devices with the
        same contype.
        """
        # set modules (1 Waveform Config & 1 6K Config)
        self.f.add_module('Waveform',
                          {'n_configs': 1, 'sn_size': 100})
        self.f.add_module('6K Compumotor',
                          {'n_configs': 1, 'sn_size': 100})
        _lapdf = self.lapdf

        # fake 6K as contype.waveform
        _lapdf.file_map.controls['6K Compumotor'].info['contype'] = \
            _lapdf.file_map.controls['Waveform'].info['contype']

        # test
        self.assertRaises(TypeError,
                          condition_controls,
                          _lapdf, ['Waveform', '6K Compumotor'])


if __name__ == '__main__':
    ut.main()
