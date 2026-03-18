"""
Module containing the HDF5 reader for files generated in the Physics
180E class.
"""

__all__ = ["File"]

from bapsflib._hdf.utils.file import File as BaseFile


class File(BaseFile):
    """Open a HDF5 file created by the Physics 180E class."""

    def __init__(self, name: str, mode="r", silent=False, **kwargs):
        """
        Parameters
        ----------
        name : `str`
            name (and path) of file on disk

        mode : `str`, optional
            readonly ``'r'`` (DEFAULT) and read/write ``'r+'``

        silent : `bool`, optional
            set `True` to suppress warnings (`False` DEFAULT)

        kwargs : `dict`, optional
            additional keywords passed on to `h5py.File`

        Examples
        --------

        >>> # open HDF5 file
        >>> f = File('sample.hdf5')
        >>>>
        >>> # the File class is a subclass of h5py.File
        >>> isinstance(f, h5py.File)
        True
        """
        control_path = (
            "Control" if "control_path" not in kwargs else kwargs["control_path"]
        )
        digitizer_path = (
            "Acquisition" if "digitizer_path" not in kwargs else kwargs["digitizer_path"]
        )
        msi_path = "/" if "msi_path" not in kwargs else kwargs["msi_path"]

        super().__init__(
            name,
            mode=mode,
            control_path=control_path,
            digitizer_path=digitizer_path,
            msi_path=msi_path,
            silent=silent,
            **kwargs
        )
