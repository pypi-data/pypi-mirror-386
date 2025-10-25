# -*- coding: utf-8 -*-
# Copyright 2024 Matthew Fitzpatrick.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
"""``h5pywrappers`` is a simple Python library that contains several functions
used to facilitate loading data from and saving data to HDF5 files. These
functions are wrappers that call functions from the `h5py
<https://docs.h5py.org/en/stable/>`_ library.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# Import child modules and packages of current package.
import h5pywrappers.obj
import h5pywrappers.group
import h5pywrappers.dataset
import h5pywrappers.datasubset
import h5pywrappers.scalar
import h5pywrappers.json
import h5pywrappers.attr

# Get version of current package.
from h5pywrappers.version import __version__



##################################
## Define classes and functions ##
##################################

# List of public objects in package.
__all__ = []



###########################
## Define error messages ##
###########################
