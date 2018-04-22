#!/usr/bin/env python3

from setuptools import setup, find_packages

CLASSIFIERS = """
Development Status :: 2 - Pre-Alpha
Intended Audience :: Developers
Intended Audience :: Education
Intended Audience :: Science/Research
License :: OSI Approved :: BSD License
Natural Language :: English
Operating System :: MacOS
Operating System :: Microsoft :: Windows
Operating System :: POSIX :: Linux
Programming Language :: Python :: 3
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Topic :: Database
Topic :: Education
Topic :: Scientific/Engineering
Topic :: Scientific/Engineering :: Physics
Topic :: Software Development
Topic :: Software Development :: Libraries :: Python Modules
"""

setup(
    name='bapsflib',
    version='0.1.3.dev5',
    description='A toolkit for handling data collected at BaPSF.',
    license='BSD',
    classifiers=CLASSIFIERS,
    url='https://github.com/rocco8773/bapsflib.git#egg=bapsflib',
    author='Erik T. Everson',
    author_email='eteveson@gmail.com',
    packages=find_packages(),
    install_requires=['h5py>=2.6',
                      'numpy>=1.7',
                      'scipy >= 1.0.0'
                      'sphinx-rtd-theme>=0.3.0'],
    python_requires='>=3.5',
    zip_safe=False,
    include_package_data=True
)
