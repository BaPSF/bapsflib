APS Examples
============

>>> from bapsflib import lapd
>>> f = lapd.File('example.hdf5')
>>>
>>> # print info about the data file
>>> f.info
{'absolute file path': '/path/to/exmple.hdf5',
 'exp description': 'First experiment at BaPSF',
 'exp name': 'October2019',
 'exp set description': 'Set of experiments for User',
 'exp set name': 'Campaigns for User',
 'file': 'example.hdf5',
 'investigator': 'User',
 'lapd version': '1.2',
 'run date': '10/21/2019 5:00:00 PM',
 'run description': 'this is my first run',
 'run name': 'this_will_be_fun',
 'run status': 'Started'}


>>> # discovered MSI
>>> f.msi
{'Discharge': <bapsflib._hdf.maps.msi.discharge.HDFMapMSIDischarge at 0x128d5c4a8>,
 'Gas pressure': <bapsflib._hdf.maps.msi.gaspressure.HDFMapMSIGasPressure at 0x128d5c518>,
 'Heater': <bapsflib._hdf.maps.msi.heater.HDFMapMSIHeater at 0x128d5c5c0>,
 'Interferometer array': <bapsflib._hdf.maps.msi.interferometerarray.HDFMapMSIInterferometerArray at 0x128d5c9e8>,
 'Magnetic field': <bapsflib._hdf.maps.msi.magneticfield.HDFMapMSIMagneticField at 0x128d5ca20>}
>>>
>>> # discovered controls
>>> f.controls
{'6K Compumotor': <bapsflib._hdf.maps.controls.sixk.HDFMapControl6K at 0x128d5cf98>}
>>>
>>> # discovered digitizers
>>> f.controls
{'SIS crate': <bapsflib._hdf.maps.digitizers.siscrate.HDFMapDigiSISCrate at 0x128d5cdd8>}

>>> # Reading MSI - Magnetic field
>>> mdata = f.read_msi('Magnetic field')
>>>
>>> # data is always returned as a structured numpy array
>>> isinstance(mdata, numpy.ndarray)
True
>>> mdata.dtype.names
('shotnum', 'magnet ps current', 'magnetic field', 'meta')
>>>
>>> # data is always returned with a 'info' attribute
>>> # to give the data's origin and meta-info
>>> mdata.info
{'calib tag': [b'08/27/2013'],
 'device group path': '/MSI/Magnetic field',
 'device name': 'Magnetic field',
 'source file': '/Users/erik/Documents/Research_BaPSF/Projects_Python/test_hdfFiles/p21plane.hdf5',
 'z': array([-300.     , -297.727  , -295.45395, ..., 2020.754  , 2023.027  ,
        2025.3    ], dtype=float32)}

>>> # Reading data w/ position data
>>> data = f.read_data(1, 1, shotnum=1, add_controls=['6K Compumotor'])
>>>
>>> # data is always returned as a structured numpy array
>>> isinstance(data, numpy.ndarray)
True
>>> data.dtype.names
('shotnum', 'signal', 'xyz', 'ptip_rot_theta', 'ptip_rot_phi')
>>>
>>> # data is always returned with a 'info' attribute
>>> # to give the data's origin and meta-info
>>> data.info
{'adc': 'SIS 3302',
 'bit': 16,
 'board': 1,
 'channel': 1,
 'clock rate': <Quantity 100. MHz>,
 'configuration name': 'config01',
 'controls': {'6K Compumotor': {...}},
 'device dataset path': '/Raw data + config/SIS crate/config01 [Slot 5: SIS 3302 ch 1]',
 'device group path': '/Raw data + config/SIS crate',
 'digitizer': 'SIS crate',
 'port': (None, None),
 'probe name': None,
 'sample average': 8,
 'shot average': None,
 'signal units': Unit("V"),
 'source file': '/path/to/example.hdf5',
 'voltage offset': <Quantity -2.531 V>}
