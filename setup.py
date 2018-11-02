#!/usr/bin/env python3
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
import codecs
import os
import re

from setuptools import setup, find_packages

# find here
here = os.path.abspath(os.path.dirname(__file__))

# define CLASSIFIERS
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: Education",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: BSD License",
    "Natural Language :: English",
    "Operating System :: MacOS",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Education",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Physics",
    "Topic :: Software Development",
    "Topic :: Software Development :: Libraries :: Python Modules",
]


# ---- Define helpers for version-ing                               ----
# - following 'Single-sourcing the package version' from 'Python
#   Packaging User Guide'
#   https://packaging.python.org/guides/single-sourcing-package-version/
#
def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# ---- Define long description                                      ----
with open('README.md', 'r') as fh:
    LONG_DESCRIPTION = fh.read()

# ---- Perform setup                                                ----
setup(
    name='bapsflib',
    version=find_version("bapsflib", "__init__.py"),
    description='A toolkit for handling data collected at BaPSF.',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    scripts=[],
    setup_requires=['astropy>=2.0',
                    'h5py>=2.6',
                    'numpy>=1.7',
                    'scipy>=1.0.0'],
    install_requires=['astropy>=2.0',
                      'h5py>=2.6',
                      'numpy>=1.7',
                      'scipy>=1.0.0'],
    python_requires='>=3.5',
    author='Erik T. Everson',
    author_email='eteveson@gmail.com',
    license='3-clause BSD',
    url='https://github.com/BaPSF/bapsflib',
    keywords=['bapsf', 'HDF5', 'lapd', 'physics', 'plasma', 'science'],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    package_urls={
        "BaPSF": "http://plasma.physics.ucla.edu/",
        "Documentation": "https://bapsflib.readthedocs.io/en/latest/",
        "GitHub": "https://github.com/BaPSF/bapsflib",
    }
)
