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
r"""Contains tests for the module :mod:`h5pywrappers.dataset`.

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



##################################
## Define classes and functions ##
##################################



def test_1_of_save():
    dataset_candidates = (np.random.rand(2, 3),
                          "hello world",
                          ((1,), (2, 3)))

    for dataset_candidate in dataset_candidates:
        dataset_id = h5pywrappers.obj.ID(filename="./test_data/test_file.h5",
                                         path_in_file="group_1/dataset_1")

        kwargs = {"dataset": dataset_candidate,
                  "dataset_id": dataset_id,
                  "write_mode": "w"}
        if isinstance(dataset_candidate, tuple):
            with pytest.raises(TypeError) as err_info:
                h5pywrappers.dataset.save(**kwargs)
        else:
            h5pywrappers.dataset.save(**kwargs)

    filename = dataset_id.core_attrs["filename"]
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



def test_2_of_save():
    np_array = np.random.rand(2, 3)

    dataset_id = h5pywrappers.obj.ID(filename="./test_data/test_file.h5",
                                     path_in_file="group_1/dataset_1")

    write_modes = ("w", "a", "w-", "a-")

    for write_mode in write_modes:
        print(write_mode)
        kwargs = {"dataset": np_array,
                  "dataset_id": dataset_id,
                  "write_mode": write_mode}
        
        if write_mode in ("w", "a"):
            h5pywrappers.dataset.save(**kwargs)
        else:
            with pytest.raises(IOError) as err_info:
                h5pywrappers.dataset.save(**kwargs)

    filename = dataset_id.core_attrs["filename"]
    pathlib.Path(filename).unlink()

    kwargs = {"dataset": np_array, "dataset_id": dataset_id, "write_mode": "w-"}
    h5pywrappers.dataset.save(**kwargs)

    pathlib.Path(filename).unlink()
        
    kwargs = {"dataset": np_array, "dataset_id": dataset_id, "write_mode": "a-"}
    h5pywrappers.dataset.save(**kwargs)

    kwargs = {"dataset": np_array, "dataset_id": dataset_id, "write_mode": "b"}
    with pytest.raises(ValueError) as err_info:
        h5pywrappers.dataset.save(**kwargs)

    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



def test_1_of_load():
    np_array = np.random.rand(2, 3)
    filename = "./test_data/test_file.h5"

    dataset_id_1 = h5pywrappers.obj.ID(filename=filename,
                                       path_in_file="group_1/dataset_1")
    dataset_id_2 = h5pywrappers.obj.ID(filename=filename,
                                       path_in_file="group_1/dataset_2")
    dataset_id_3 = h5pywrappers.obj.ID(filename=filename,
                                       path_in_file="group_1")

    kwargs = {"dataset": np_array,
              "dataset_id": dataset_id_1,
              "write_mode": "a-"}
    h5pywrappers.dataset.save(**kwargs)

    kwargs = {"dataset_id": dataset_id_1, "read_only": False}
    dataset_1 = h5pywrappers.dataset.load(**kwargs)

    dataset_1[0, 0] = 0
    
    kwargs = {"dataset": dataset_1,
              "dataset_id": dataset_id_2,
              "write_mode": "a-"}
    h5pywrappers.dataset.save(**kwargs)

    dataset_1.file.close()

    kwargs = {"dataset_id": dataset_id_1, "read_only": True}
    dataset_1 = h5pywrappers.dataset.load(**kwargs)

    kwargs = {"dataset_id": dataset_id_2, "read_only": True}
    dataset_2 = h5pywrappers.dataset.load(**kwargs)

    assert np.all(dataset_1[()] == dataset_2[()])

    dataset_1.file.close()
    dataset_2.file.close()

    kwargs = {"dataset_id": dataset_id_3, "read_only": True}
    with pytest.raises(TypeError) as err_info:
        group_1 = h5pywrappers.dataset.load(**kwargs)

    kwargs = {"dataset_id": dataset_id_1, "read_only": None}
    with pytest.raises(TypeError) as err_info:
        dataset_1 = h5pywrappers.dataset.load(**kwargs)

    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



###########################
## Define error messages ##
###########################
