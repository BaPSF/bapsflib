import unittest as ut

from bapsflib._hdf.utils.file import File as BaseFile
from bapsflib._hdf.utils.tests import TestBase
from bapsflib.phys180E._hdf.file_ import File


class TestPhys180EFile(TestBase):
    """
    Test case for :class:`~bapsflib.phys180E._hdf.file.File`
    """

    def setUp(self):
        super().setUp()
        self._bf = File(self.f.filename, silent=True)

    def tearDown(self):
        self._bf.close()
        super().tearDown()

    @property
    def bf(self) -> File | None:
        if not hasattr(self, "_bf"):
            return

        return self._bf

    @property
    def control_path(self) -> str:
        return "Control"

    @property
    def digitizer_path(self) -> str:
        return "Acquisition"

    @property
    def msi_path(self) -> str:
        return "/"

    def test_inheritance(self):
        self.assertTrue(issubclass(File, BaseFile))

    def test_control_path(self):
        self.assertEqual(self.bf.CONTROL_PATH, self.control_path)

    def test_digitizer_path(self):
        self.assertEqual(self.bf.DIGITIZER_PATH, self.digitizer_path)

    def test_msi_path(self):
        self.assertEqual(self.bf.MSI_PATH, self.msi_path)
