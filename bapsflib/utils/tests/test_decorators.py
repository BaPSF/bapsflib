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
import inspect
import unittest as ut

from unittest import mock

from bapsflib._hdf import File as BaPSFFile
from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib.lapd import File as LaPDFile
from bapsflib.utils.decorators import with_bf, with_lapdf


class TestWithBF(ut.TestCase):
    """
    Test case for decorator :func:`~bapsflib.utils.decorators.with_bf`.
    """

    f = NotImplemented  # type: FauxHDFBuilder

    @classmethod
    def setUpClass(cls) -> None:
        # create HDF5 file
        super().setUpClass()
        cls.f = FauxHDFBuilder()

    def setUp(self) -> None:
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()
        self.f.reset()

    @classmethod
    def tearDownClass(cls) -> None:
        # cleanup and close HDF5 file
        super().tearDownClass()
        cls.f.cleanup()

    @property
    def filename(self) -> str:
        return self.f.filename

    @mock.patch(
        f"{BaPSFFile.__module__}.{BaPSFFile.__qualname__}",
        side_effect=BaPSFFile,
        autospec=True,
    )
    def test_settings_by_decorator_kwargs(self, mock_bf_class):
        # create a function to mock
        def foo(bf: BaPSFFile, **kwargs):
            self.assertIsInstance(bf, BaPSFFile)
            bapsf_settings = {
                "filename": bf.filename,
                "control_path": bf.CONTROL_PATH,
                "digitizer_path": bf.DIGITIZER_PATH,
                "msi_path": bf.MSI_PATH,
            }
            return bapsf_settings

        mock_foo = mock.Mock(side_effect=foo, name="mock_foo", autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        # define file settings to be based to decorator
        settings = {
            "filename": self.filename,
            "control_path": "Raw data + config",
            "digitizer_path": "Raw data + config",
            "msi_path": "MSI",
        }

        # -- use decorator like a function --
        # wrapped_func = with_bf(func, **settings)
        func = with_bf(mock_foo, **settings)
        bf_settings = func()
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        for name in settings:
            self.assertEqual(settings[name], bf_settings[name])

        # reset mocks
        mock_foo.reset_mock()
        mock_bf_class.reset_mock()

        # -- mimic sugar syntax use of the decorator --
        #
        # @with_bf(**settings)
        #     def foo(bf):
        #         pass
        #
        func = with_bf(**settings)(mock_foo)
        bf_settings = func()
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        for name in settings:
            self.assertEqual(settings[name], bf_settings[name])

        # reset mocks
        mock_foo.reset_mock()
        mock_bf_class.reset_mock()

        # -- function keywords override decorator settings --
        bf_settings = func(control_path="a different path")
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        self.assertEqual("a different path", bf_settings["control_path"])
        for name in settings:
            if name == "control_path":
                continue
            self.assertEqual(settings[name], bf_settings[name])

        # reset mocks
        mock_foo.reset_mock()
        mock_bf_class.reset_mock()

        # -- ValueError if filename never passed --
        # update settings s.t. no filename is specified
        fname = settings.pop("filename")

        # wrap and test
        func = with_bf(**settings)(mock_foo)
        self.assertRaises(ValueError, func)

        # reset
        settings["filename"] = fname
        mock_foo.reset_mock()
        mock_bf_class.reset_mock()

        # -- if path not specified then class default is assumed --
        # update settings s.t. no filename is specified
        cp = settings.pop("control_path")

        # wrap and test
        func = with_bf(**settings)(mock_foo)
        bf_settings = func()
        self.assertTrue(mock_foo.called)
        self.assertTrue(mock_bf_class.called)
        for name in bf_settings:
            if name == "control_path":
                cp_default = (
                    inspect.signature(BaPSFFile).parameters["control_path"].default
                )
                self.assertEqual(bf_settings[name], cp_default)
            else:
                self.assertEqual(bf_settings[name], settings[name])

        # reset
        settings["control_path"] = cp
        mock_foo.reset_mock()
        mock_bf_class.reset_mock()

        # -- function arguments also override decorator settings --
        # create a function to mock
        def foo(filename: str, bf: BaPSFFile):
            self.assertIsInstance(bf, BaPSFFile)
            bapsf_settings = {
                "filename": bf.filename,
                "control_path": bf.CONTROL_PATH,
                "digitizer_path": bf.DIGITIZER_PATH,
                "msi_path": bf.MSI_PATH,
            }
            return bapsf_settings

        mock_foo = mock.Mock(side_effect=foo, name="mock_foo", autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        fname = settings.pop("filename")
        settings["filename"] = "not a real file"

        # wrap and test
        func = with_bf(**settings)(mock_foo)
        bf_settings = func(fname)
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        self.assertEqual(bf_settings["filename"], fname)
        for name in settings:
            if name == "filename":
                continue
            self.assertEqual(settings[name], bf_settings[name])

        # reset mocks
        settings["filename"] = fname
        mock_foo.reset_mock()
        mock_bf_class.reset_mock()

    @mock.patch(
        f"{BaPSFFile.__module__}.{BaPSFFile.__qualname__}",
        side_effect=BaPSFFile,
        autospec=True,
    )
    def test_settings_by_function_args(self, mock_bf_class):
        # BaPSF file settings can also be pass by either function args or
        # kwargs
        #
        # define file settings to be based to decorator
        settings = {
            "filename": self.filename,
            "control_path": "Raw data + config",
            "digitizer_path": "Raw data + config",
            "msi_path": "MSI",
        }

        # create a function to mock
        def foo(filename: str, bf: BaPSFFile, **kwargs):
            self.assertIsInstance(bf, BaPSFFile)
            bapsf_settings = {
                "filename": bf.filename,
                "control_path": bf.CONTROL_PATH,
                "digitizer_path": bf.DIGITIZER_PATH,
                "msi_path": bf.MSI_PATH,
            }
            return bapsf_settings

        # define function mock
        mock_foo = mock.Mock(side_effect=foo, name="mock_foo", autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        # wrap and test
        # - this is equivalent to writing
        #
        #     @with_bf
        #     def foo(filename, bf, **kwargs):
        #         pass
        #
        fname = settings.pop("filename")
        func = with_bf(mock_foo)
        bf_settings = func(fname, **settings)
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        for name in bf_settings:
            if name == "filename":
                self.assertEqual(bf_settings[name], fname)
            else:
                self.assertEqual(bf_settings[name], settings[name])

        # reset mocks
        mock_bf_class.reset_mock()
        mock_foo.reset_mock()

        # settings defines 'control_path'=None
        settings["control_path"] = None
        bf_settings = func(fname, **settings)
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(mock_foo.called)
        self.assertEqual(
            bf_settings["control_path"],
            inspect.signature(BaPSFFile).parameters["control_path"].default,
        )

        # reset mocks
        mock_bf_class.reset_mock()
        mock_foo.reset_mock()

        # settings defines 'filename'=None
        self.assertRaises(ValueError, func, None)

    @mock.patch(
        f"{BaPSFFile.__module__}.{BaPSFFile.__qualname__}",
        side_effect=BaPSFFile,
        autospec=True,
    )
    def test_settings_by_method_self(self, mock_bf_class):
        # create class/method to mock
        class Something(object):
            def __init__(self, **kwargs):
                super().__init__()
                self.filename = kwargs.get("filename", None)
                self.control_path = kwargs.get("control_path", None)
                self.digitizer_path = kwargs.get("digitizer_path", None)
                self.msi_path = kwargs.get("msi_path", None)

            @with_bf
            def foo(self, bf: BaPSFFile, **kwargs):
                bapsf_settings = {
                    "filename": bf.filename,
                    "control_path": bf.CONTROL_PATH,
                    "digitizer_path": bf.DIGITIZER_PATH,
                    "msi_path": bf.MSI_PATH,
                }
                return isinstance(bf, BaPSFFile), bapsf_settings

        # define file settings
        settings = {
            "filename": self.filename,
            "control_path": "Raw data + config",
            "digitizer_path": "Raw data + config",
            "msi_path": "MSI",
        }

        # functional call
        sthing = Something(**settings)
        bf_settings = sthing.foo()
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(bf_settings[0])
        for name in bf_settings[1]:
            self.assertEqual(bf_settings[1][name], settings[name])
        mock_bf_class.reset_mock()

        # keywords still override self
        bf_settings = sthing.foo(control_path="a new path")
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(bf_settings[0])
        self.assertEqual(bf_settings[1]["control_path"], "a new path")
        mock_bf_class.reset_mock()

        # missing 'control_path'
        cp = settings.pop("control_path")
        sthing = Something(**settings)
        bf_settings = sthing.foo()
        self.assertTrue(mock_bf_class.called)
        self.assertTrue(bf_settings[0])
        self.assertEqual(
            bf_settings[1]["control_path"],
            inspect.signature(BaPSFFile).parameters["control_path"].default,
        )
        mock_bf_class.reset_mock()


class TestWithLaPDF(ut.TestCase):
    """
    Test case for decorator :func:`~bapsflib.utils.decorators.with_lapdf`.
    """

    f = NotImplemented  # type: FauxHDFBuilder

    @classmethod
    def setUpClass(cls) -> None:
        # create HDF5 file
        super().setUpClass()
        cls.f = FauxHDFBuilder()

    def setUp(self) -> None:
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()
        self.f.reset()

    @classmethod
    def tearDownClass(cls) -> None:
        # cleanup and close HDF5 file
        super().tearDownClass()
        cls.f.cleanup()

    @property
    def filename(self) -> str:
        return self.f.filename

    @mock.patch(
        f"{LaPDFile.__module__}.{LaPDFile.__qualname__}",
        side_effect=LaPDFile,
        autospec=True,
    )
    def test_settings_by_decorator_kwargs(self, mock_lapdf_class):
        # create a function to mock
        def foo(lapdf: LaPDFile, **kwargs):
            self.assertIsInstance(lapdf, LaPDFile)
            f_settings = {
                "filename": lapdf.filename,
                "control_path": lapdf.CONTROL_PATH,
                "digitizer_path": lapdf.DIGITIZER_PATH,
                "msi_path": lapdf.MSI_PATH,
            }
            return f_settings

        mock_foo = mock.Mock(side_effect=foo, name="mock_foo", autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        # define file settings to be based to decorator
        settings = {"filename": self.filename}

        # -- use decorator like a function --
        # wrapped_func = with_lapdf(func, **settings)
        func = with_lapdf(mock_foo, **settings)
        lapdf_settings = func()
        self.assertTrue(mock_lapdf_class.called)
        self.assertTrue(mock_foo.called)
        for name in settings:
            self.assertEqual(settings[name], lapdf_settings[name])

        # reset mocks
        mock_foo.reset_mock()
        mock_lapdf_class.reset_mock()

        # -- mimic sugar syntax use of the decorator --
        #
        # @with_lapdf(**settings)
        #     def foo(bf):
        #         pass
        #
        func = with_lapdf(**settings)(mock_foo)
        lapdf_settings = func()
        self.assertTrue(mock_lapdf_class.called)
        self.assertTrue(mock_foo.called)
        for name in settings:
            self.assertEqual(settings[name], lapdf_settings[name])

        # reset mocks
        mock_foo.reset_mock()
        mock_lapdf_class.reset_mock()

        # -- function keywords override decorator settings --
        fname = settings.pop("filename")
        settings["filename"] = "not a real file"
        func = with_lapdf(**settings)(mock_foo)
        lapdf_settings = func(filename=fname)
        self.assertTrue(mock_lapdf_class.called)
        self.assertTrue(mock_foo.called)
        self.assertEqual(lapdf_settings["filename"], fname)

        # reset mocks
        settings["filename"] = fname
        mock_foo.reset_mock()
        mock_lapdf_class.reset_mock()

        # -- ValueError if filename never passed --
        # update settings s.t. no filename is specified
        fname = settings.pop("filename")

        # wrap and test
        func = with_lapdf(**settings)(mock_foo)
        self.assertRaises(ValueError, func)

        # reset
        settings["filename"] = fname
        mock_foo.reset_mock()
        mock_lapdf_class.reset_mock()

        # -- function arguments also override decorator settings --
        # create a function to mock
        def foo(filename: str, lapdf: LaPDFile):
            self.assertIsInstance(lapdf, LaPDFile)
            f_settings = {
                "filename": lapdf.filename,
                "control_path": lapdf.CONTROL_PATH,
                "digitizer_path": lapdf.DIGITIZER_PATH,
                "msi_path": lapdf.MSI_PATH,
            }
            return f_settings

        mock_foo = mock.Mock(side_effect=foo, name="mock_foo", autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        fname = settings.pop("filename")
        settings["filename"] = "not a real file"

        # wrap and test
        func = with_lapdf(**settings)(mock_foo)
        lapdf_settings = func(fname)
        self.assertTrue(mock_lapdf_class.called)
        self.assertTrue(mock_foo.called)
        self.assertEqual(lapdf_settings["filename"], fname)

        # reset mocks
        settings["filename"] = fname
        mock_foo.reset_mock()
        mock_lapdf_class.reset_mock()

    @mock.patch(
        f"{LaPDFile.__module__}.{LaPDFile.__qualname__}",
        side_effect=LaPDFile,
        autospec=True,
    )
    def test_settings_by_function_args(self, mock_lapdf_class):
        # LaPD file settings can also be pass by either function args or
        # kwargs
        #
        # define file settings to be based to decorator
        settings = {"filename": self.filename}

        # create a function to mock
        def foo(filename: str, lapdf: LaPDFile, **kwargs):
            self.assertIsInstance(lapdf, LaPDFile)
            f_settings = {
                "filename": lapdf.filename,
                "control_path": lapdf.CONTROL_PATH,
                "digitizer_path": lapdf.DIGITIZER_PATH,
                "msi_path": lapdf.MSI_PATH,
            }
            return f_settings

        # define function mock
        mock_foo = mock.Mock(side_effect=foo, name="mock_foo", autospec=True)
        mock_foo.__signature__ = inspect.signature(foo)

        # wrap and test
        # - this is equivalent to writing
        #
        #     @with_bf
        #     def foo(filename, bf, **kwargs):
        #         pass
        #
        fname = settings.pop("filename")
        func = with_lapdf(mock_foo)
        lapdf_settings = func(fname, **settings)
        self.assertTrue(mock_lapdf_class.called)
        self.assertTrue(mock_foo.called)
        self.assertEqual(lapdf_settings["filename"], fname)

        # reset mocks
        settings["filename"] = fname
        mock_lapdf_class.reset_mock()
        mock_foo.reset_mock()

        # settings defines 'filename'=None
        self.assertRaises(ValueError, func, None)

    @mock.patch(
        f"{LaPDFile.__module__}.{LaPDFile.__qualname__}",
        side_effect=LaPDFile,
        autospec=True,
    )
    def test_settings_by_method_self(self, mock_lapdf_class):
        # create class/method to mock
        class Something(object):
            def __init__(self, **kwargs):
                super().__init__()
                self.filename = kwargs.get("filename", None)
                self.control_path = kwargs.get("control_path", None)
                self.digitizer_path = kwargs.get("digitizer_path", None)
                self.msi_path = kwargs.get("msi_path", None)

            @with_lapdf
            def foo(self, lapdf: LaPDFile, **kwargs):
                f_settings = {
                    "filename": lapdf.filename,
                    "control_path": lapdf.CONTROL_PATH,
                    "digitizer_path": lapdf.DIGITIZER_PATH,
                    "msi_path": lapdf.MSI_PATH,
                }
                return isinstance(lapdf, LaPDFile), f_settings

        # define file settings
        settings = {"filename": self.filename}

        # functional call
        sthing = Something(**settings)
        lapdf_settings = sthing.foo()
        self.assertTrue(mock_lapdf_class.called)
        self.assertTrue(lapdf_settings[0])
        self.assertEqual(lapdf_settings[1]["filename"], settings["filename"])
        mock_lapdf_class.reset_mock()

        # keywords still override self
        fname = settings.pop("filename")
        sthing = Something(**settings)
        lapdf_settings = sthing.foo(filename=fname)
        self.assertTrue(mock_lapdf_class.called)
        self.assertTrue(lapdf_settings[0])
        self.assertEqual(lapdf_settings[1]["filename"], fname)
        settings["filename"] = fname
        mock_lapdf_class.reset_mock()


if __name__ == "__main__":
    ut.main()
