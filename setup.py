#!/usr/bin/env python

import os

from distutils.core import setup
from distutils.sysconfig import get_python_lib

from src.silver import __version__, __prog__

pkgs_path = get_python_lib()
app_name = 'silver'

setup(name=__prog__,
    version=__version__,
    description='Python Development Camps',
    author='Clint Savage',
    author_email='herlo1@gmail.com',
    url='https://github.com/herlo/Silver',
    packages=['silver', 'silver.config', 'silver.contrib', 'silver.contrib.hooks'],
    package_dir={'silver': 'src/silver'},
    scripts=['ag', 'pc'],
    package_data={'silver.config': ['settings.py.sample']},
)
