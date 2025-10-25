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
r"""Contains tests for the module :mod:`h5pywrappers.json.document`.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For deserializing JSON documents.
import json

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

# For loading and saving JSON documents objects.
import h5pywrappers.json.document



##################################
## Define classes and functions ##
##################################



@pytest.fixture
def json_document_id():
    fixture_output = h5pywrappers.obj.ID(filename="./test_data/test_file.h5",
                                         path_in_file="group_1/json_document_1")

    return fixture_output



def test_1_of_load(json_document_id):
    json_document_A = json_document_id.pre_serialize()
    serialized_json_document = json.dumps(json_document_A)

    kwargs = {"dataset": serialized_json_document,
              "dataset_id": json_document_id,
              "write_mode": "w"}
    h5pywrappers.dataset.save(**kwargs)

    json_document_B = h5pywrappers.json.document.load(json_document_id)

    assert json_document_A == json_document_B

    kwargs = {"dataset": b"[1,2,3]",
              "dataset_id": json_document_id,
              "write_mode": "w"}
    h5pywrappers.dataset.save(**kwargs)

    with pytest.raises(TypeError) as err_info:
        h5pywrappers.json.document.load(json_document_id)

    filename = json_document_id.core_attrs["filename"]
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



def test_1_of_save(json_document_id):
    json_document_A = json_document_id.pre_serialize()

    kwargs = {"json_document": json_document_A,
              "json_document_id": json_document_id,
              "write_mode": "w"}
    h5pywrappers.json.document.save(**kwargs)

    json_document_B = h5pywrappers.json.document.load(json_document_id)

    assert json_document_A == json_document_B

    kwargs = {"dataset_id": json_document_id, "read_only": False}
    json_document_C = h5pywrappers.dataset.load(**kwargs)

    kwargs = {"json_document": json_document_C,
              "json_document_id": json_document_id,
              "write_mode": "a"}
    h5pywrappers.json.document.save(**kwargs)

    json_document_C.file.close()

    json_document_D = h5pywrappers.json.document.load(json_document_id)

    assert json_document_A == json_document_D

    with pytest.raises(TypeError) as err_info:
        kwargs = {"json_document": None,
                  "json_document_id": json_document_id,
                  "write_mode": "w"}
        h5pywrappers.json.document.save(**kwargs)
    
    kwargs = {"dataset": b"[1, 2, 3]",
              "dataset_id": json_document_id,
              "write_mode": "w"}
    h5pywrappers.dataset.save(**kwargs)

    kwargs = {"dataset_id": json_document_id, "read_only": False}
    dataset = h5pywrappers.dataset.load(**kwargs)

    with pytest.raises(TypeError) as err_info:
        kwargs = {"json_document": dataset,
                  "json_document_id": json_document_id,
                  "write_mode": "a"}
        h5pywrappers.json.document.save(**kwargs)

    filename = json_document_id.core_attrs["filename"]
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



###########################
## Define error messages ##
###########################
