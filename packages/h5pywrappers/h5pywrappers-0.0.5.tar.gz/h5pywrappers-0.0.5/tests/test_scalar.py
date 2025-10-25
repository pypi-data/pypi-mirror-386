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
r"""Contains tests for the module :mod:`h5pywrappers.scalar`.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For removing files.
import pathlib

# For removing directories.
import shutil



# For general array handling.
import numpy as np

# For operations related to unit tests.
import pytest



# For loading and saving HDF5 objects.
import h5pywrappers.obj

# For loading and saving HDF5 datasets.
import h5pywrappers.dataset

# For loading and saving HDF5 scalars.
import h5pywrappers.scalar



##################################
## Define classes and functions ##
##################################



@pytest.fixture
def scalar_candidate_set_1():
    fixture_output = (np.random.rand(2, 3), "hello world")

    return fixture_output



@pytest.fixture
def scalar_candidate_set_2():
    fixture_output = (1.5, 1.5+0.0j, 1.5+2.5j, np.array(1.5+2.5j))

    return fixture_output



@pytest.fixture
def scalar_id():
    fixture_output = h5pywrappers.obj.ID(filename="./test_data/test_file.h5",
                                         path_in_file="group_1/scalar_1")

    return fixture_output



def test_1_of_load(scalar_candidate_set_1, scalar_id, scalar_candidate_set_2):
    for scalar_candidate in scalar_candidate_set_1:
        kwargs = {"dataset": scalar_candidate,
                  "dataset_id": scalar_id,
                  "write_mode": "w"}
        h5pywrappers.dataset.save(**kwargs)

        with pytest.raises(TypeError) as err_info:
            h5pywrappers.scalar.load(scalar_id)

    for scalar_candidate in scalar_candidate_set_2:
        kwargs = {"dataset": scalar_candidate,
                  "dataset_id": scalar_id,
                  "write_mode": "w"}
        h5pywrappers.dataset.save(**kwargs)

        scalar_A = (float(np.array(scalar_candidate, dtype="complex").real)
                    if (np.array(scalar_candidate, dtype="complex").imag == 0)
                    else complex(scalar_candidate))            
        scalar_B = h5pywrappers.scalar.load(scalar_id)

        assert scalar_A == scalar_B

    filename = scalar_id.core_attrs["filename"]
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



def test_1_of_save(scalar_candidate_set_1, scalar_id, scalar_candidate_set_2):
    for scalar_candidate in scalar_candidate_set_1:
        with pytest.raises(TypeError) as err_info:
            kwargs = {"scalar": scalar_candidate,
                      "scalar_id": scalar_id,
                      "write_mode": "w"}
            h5pywrappers.scalar.save(**kwargs)

    for scalar_candidate in scalar_candidate_set_2:
        kwargs = {"scalar": scalar_candidate,
                  "scalar_id": scalar_id,
                  "write_mode": "w"}
        h5pywrappers.scalar.save(**kwargs)

        scalar_A = (float(np.array(scalar_candidate, dtype="complex").real)
                    if (np.array(scalar_candidate, dtype="complex").imag == 0)
                    else complex(scalar_candidate))            
        scalar_B = h5pywrappers.scalar.load(scalar_id)

        assert scalar_A == scalar_B

    filename = scalar_id.core_attrs["filename"]
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



###########################
## Define error messages ##
###########################
