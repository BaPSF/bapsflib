#!/usr/bin/env python

from setuptools import setup

CLASSIFIERS = \
"""
Development Status :: 2 - Pre-Alpha
Intended Audience :: Developers
Intended Audience :: Education
Intended Audience :: Science/Research
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
    version='0.1.2.dev',
    description='A toolkit for handling data collected at BaPSF.',
    classifiers=CLASSIFIERS,
    url='https://github.com/rocco8773/bapsflib',
    author='Erik T. Everson',
    author_email='eteveson@gmail.com',
    zip_safe=False,
    include_package_data=True
)
