#!/usr/bin/env python

from setuptools import setup, Extension
version='0.3'
setup(name='PythonForPicam',
      version=version,
      description='Setup Tools version of PythonForPicam (Joe Lowney 2013)',
      long_description = """
      PythonForPicam is a Python ctypes interface to the Princeton Instruments PICAM Library 
      Copyright (C) 2013 Joe Lowney. The copyright holder can be reached at joelowney@gmail.com

      This program is free software: you can redistribute it and/or modify it under the terms of 
      the GNU General Public License as published by the Free Software Foundation, either version 3 
      of the License, or any later version.

      This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
      without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
      See the GNU General Public License for more details.

      You should have received a copy of the GNU General Public License along with this program. 
      If not, see http://www.gnu.org/licenses/.
      """,
      author='Joe Lowney,Josh Stillerman',
      author_email='jas@psfc.mit.edu',
      package_dir = {'PythonForPicam':'.',},
      include_package_data = False,
      packages = ['PythonForPicam',],
      platforms = ('Windows'),
      url = 'https://github.com/joshStillerman/PythonForPicam',
      classifiers = [ 'Development Status :: 4 - Beta',
      'Programming Language :: Python',
      'Intended Audience :: Science/Research',
      'Environment :: Console',
      'Topic :: Scientific/Engineering',
      ],
      keywords = ['princeton instruments','camera',],
      install_requires=['numpy'],
      zip_safe = False,
     )
