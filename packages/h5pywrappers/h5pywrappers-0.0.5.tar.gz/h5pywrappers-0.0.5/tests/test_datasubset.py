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
r"""Contains tests for the module :mod:`h5pywrappers.datasubset`.

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

# For loading and saving HDF5 datasubsets.
import h5pywrappers.datasubset



##################################
## Define classes and functions ##
##################################



@pytest.fixture
def dataset_candidate():
    fixture_output = np.random.rand(2, 5, 4, 6)

    return fixture_output



@pytest.fixture
def dataset_id():
    fixture_output = h5pywrappers.obj.ID(filename="./test_data/test_file.h5",
                                         path_in_file="group_1/dataset_1")

    return fixture_output



@pytest.fixture
def multi_dim_slice_set_1():
    fixture_output = ((1, slice(1, None, 1), [3, 0], slice(None)), None, "foo")

    return fixture_output



@pytest.fixture
def multi_dim_slice_set_2():
    fixture_output = ((1, slice(1, None, 1), [3, 0], slice(None)),
                      (1, slice(1, None, -2), [3, 0], slice(None)),
                      (1, [3, 0], slice(1, None, 1), slice(None)),
                      (1, [3, 0], slice(1, None, 1), -4),
                      (slice(1, None, 2), 1, [3, 0], -4),
                      (slice(1, None, 2), 1, [-2, 0], -4),
                      (1, [3, 0], slice(-1, None, -1), -4),
                      (1, [3, 0], slice(None, -1, -1), -4),
                      None)

    return fixture_output



@pytest.fixture
def multi_dim_slice_set_3():
    fixture_output = ((slice(1, None, 2), 1, [-2, 0]),
                      (1, slice(1, None, 1), [3, 3], slice(None)),
                      (1000, slice(1, None, 1), [3, 0], slice(None)),)

    return fixture_output



@pytest.fixture
def multi_dim_slice_set_4():
    fixture_output = ((1, slice(1, None, 1), [3, 0], slice(None)),
                      (1, slice(2, None, 1), [3, 0], slice(None)))

    return fixture_output



def test_1_of_ID(dataset_id, multi_dim_slice_set_1):
    for multi_dim_slice in multi_dim_slice_set_1:
        kwargs = {"dataset_id": dataset_id,
                  "multi_dim_slice": multi_dim_slice,
                  "skip_validation_and_conversion": False}
        if isinstance(multi_dim_slice, str):
            with pytest.raises(TypeError) as err_info:
                h5pywrappers.datasubset.ID(**kwargs)
        else:
            datasubset_id = h5pywrappers.datasubset.ID(**kwargs)
            serializable_rep = datasubset_id.pre_serialize()
            h5pywrappers.datasubset.ID.de_pre_serialize(serializable_rep)

    return None



def test_1_of_load(dataset_candidate,
                   dataset_id,
                   multi_dim_slice_set_2,
                   multi_dim_slice_set_3):
    kwargs = {"dataset": dataset_candidate,
              "dataset_id": dataset_id,
              "write_mode": "w"}
    h5pywrappers.dataset.save(**kwargs)

    for multi_dim_slice in multi_dim_slice_set_2:
        kwargs = {"dataset_id": dataset_id,
                  "multi_dim_slice": multi_dim_slice,
                  "skip_validation_and_conversion": False}
        datasubset_id = h5pywrappers.datasubset.ID(**kwargs)

        datasubset_A = (dataset_candidate[multi_dim_slice]
                        if (multi_dim_slice is not None)
                        else dataset_candidate[:])
        datasubset_B = h5pywrappers.datasubset.load(datasubset_id)
        assert np.all(datasubset_A == datasubset_B)

    for multi_dim_slice in multi_dim_slice_set_3:
        kwargs = {"dataset_id": dataset_id,
                  "multi_dim_slice": multi_dim_slice,
                  "skip_validation_and_conversion": False}
        datasubset_id = h5pywrappers.datasubset.ID(**kwargs)

        expected_exception = \
            (IndexError
             if (len(multi_dim_slice) != len(dataset_candidate.shape))
             else ValueError)

        with pytest.raises(expected_exception) as err_info:
            h5pywrappers.datasubset.load(datasubset_id)

    with pytest.raises(TypeError) as err_info:
        h5pywrappers.datasubset.load(None)

    filename = dataset_id.core_attrs["filename"]
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



def test_1_of_save(multi_dim_slice_set_2,
                   dataset_candidate,
                   dataset_id,
                   multi_dim_slice_set_3):
    for multi_dim_slice in multi_dim_slice_set_2:
        kwargs = {"dataset": dataset_candidate,
                  "dataset_id": dataset_id,
                  "write_mode": "w"}
        h5pywrappers.dataset.save(**kwargs)

        kwargs = {"dataset_id": dataset_id,
                  "multi_dim_slice": multi_dim_slice,
                  "skip_validation_and_conversion": False}
        datasubset_id = h5pywrappers.datasubset.ID(**kwargs)

        datasubset_A = (2*dataset_candidate[multi_dim_slice]
                        if (multi_dim_slice is not None)
                        else 2*dataset_candidate[:])

        kwargs = {"datasubset": datasubset_A, "datasubset_id": datasubset_id}
        h5pywrappers.datasubset.save(**kwargs)
        
        datasubset_B = h5pywrappers.datasubset.load(datasubset_id)

        assert np.all(datasubset_A == datasubset_B)

    for multi_dim_slice in multi_dim_slice_set_3:
        kwargs = {"dataset_id": dataset_id,
                  "multi_dim_slice": multi_dim_slice,
                  "skip_validation_and_conversion": False}
        datasubset_id = h5pywrappers.datasubset.ID(**kwargs)

        expected_exception = \
            (IndexError
             if (len(multi_dim_slice) != len(dataset_candidate.shape))
             else ValueError)

        with pytest.raises(expected_exception) as err_info:
            kwargs = {"datasubset": dataset_candidate[:],
                      "datasubset_id": datasubset_id}
            h5pywrappers.datasubset.save(**kwargs)

    with pytest.raises(TypeError) as err_info:
        kwargs = {"datasubset": (0, (1, 2)), "datasubset_id": datasubset_id}
        h5pywrappers.datasubset.save(**kwargs)

    filename = dataset_id.core_attrs["filename"]
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



def test_2_of_save(multi_dim_slice_set_4, dataset_candidate, dataset_id):
    multi_dim_slice = multi_dim_slice_set_4[0]
    datasubset = 1j*dataset_candidate[multi_dim_slice]

    for multi_dim_slice in multi_dim_slice_set_4:
        kwargs = {"dataset": dataset_candidate,
                  "dataset_id": dataset_id,
                  "write_mode": "w"}
        h5pywrappers.dataset.save(**kwargs)
    
        kwargs = {"dataset_id": dataset_id,
                  "multi_dim_slice": multi_dim_slice,
                  "skip_validation_and_conversion": False}
        datasubset_id = h5pywrappers.datasubset.ID(**kwargs)

        expected_exception = \
            (IOError
             if (datasubset.shape == dataset_candidate[multi_dim_slice].shape)
             else ValueError)

        with pytest.raises(expected_exception) as err_info:
            kwargs = {"datasubset": datasubset, "datasubset_id": datasubset_id}
            h5pywrappers.datasubset.save(**kwargs)

    filename = dataset_id.core_attrs["filename"]
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



###########################
## Define error messages ##
###########################
