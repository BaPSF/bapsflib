import h5py

class File(h5py.File):
    def __init__(self, name, mode='r', driver=None, libver=None, userblock_size=None, swmr=False, **kwds):
        h5py.File.__init__(self, name, mode, driver, libver, userblock_size, swmr)

    @property
    def listHDF_files(self):
        listHDF_files = []
        self.visit(listHDF_files.append)
        return listHDF_files
