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
r"""Contains tests for the module :mod:`h5pywrappers.attr`.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For removing files.
import pathlib

# For removing directories.
import shutil



# For operations related to unit tests.
import pytest



# For loading and saving HDF5 objects.
import h5pywrappers.obj

# For loading and saving HDF5 scalars.
import h5pywrappers.scalar

# For loading and saving HDF5 object attributes.
import h5pywrappers.attr



##################################
## Define classes and functions ##
##################################



@pytest.fixture
def obj_id():
    fixture_output = h5pywrappers.obj.ID(filename="./test_data/test_file.h5",
                                         path_in_file="group_1/scalar_1")

    return fixture_output



def test_1_of_ID(obj_id):
    kwargs = {"obj_id": obj_id,
              "attr_name": "units",
              "skip_validation_and_conversion": False}
    attr_id = h5pywrappers.attr.ID(**kwargs)

    serializable_rep = attr_id.pre_serialize()
    h5pywrappers.attr.ID.de_pre_serialize(serializable_rep)

    with pytest.raises(TypeError) as err_info:
        kwargs = {"obj_id": obj_id,
                  "attr_name": None,
                  "skip_validation_and_conversion": False}
        h5pywrappers.attr.ID(**kwargs)

    return None



def test_1_of_load(obj_id):
    kwargs = {"scalar": 1.0,
              "scalar_id": obj_id,
              "write_mode": "w"}
    h5pywrappers.scalar.save(**kwargs)

    attr_A = "m"
    attr_name = "units"

    kwargs = {"obj_id": obj_id,
              "attr_name": attr_name,
              "skip_validation_and_conversion": False}
    attr_id = h5pywrappers.attr.ID(**kwargs)

    kwargs = {"obj_id": obj_id, "read_only": False}
    obj = h5pywrappers.obj.load(**kwargs)
    obj.attrs[attr_name] = "m"
    obj.file.close()

    attr_B = h5pywrappers.attr.load(attr_id)
    
    assert attr_A == attr_B

    kwargs = {"obj_id": obj_id,
              "attr_name": "not_an_attr_name",
              "skip_validation_and_conversion": False}
    attr_id = h5pywrappers.attr.ID(**kwargs)

    with pytest.raises(ValueError) as err_info:
        h5pywrappers.attr.load(attr_id)

    filename = obj_id.core_attrs["filename"]
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



def test_1_of_save(obj_id):
    kwargs = {"scalar": 1.0,
              "scalar_id": obj_id,
              "write_mode": "w"}
    h5pywrappers.scalar.save(**kwargs)

    kwargs = {"obj_id": obj_id,
              "attr_name": "units",
              "skip_validation_and_conversion": False}
    attr_id = h5pywrappers.attr.ID(**kwargs)

    attr_A = "m"

    kwargs = {"attr": attr_A, "attr_id": attr_id, "write_mode": "a"}
    h5pywrappers.attr.save(**kwargs)

    attr_B = h5pywrappers.attr.load(attr_id)

    assert attr_A == attr_B

    attr_C = "cm"

    kwargs = {"attr": attr_C, "attr_id": attr_id, "write_mode": "a"}
    h5pywrappers.attr.save(**kwargs)

    attr_D = h5pywrappers.attr.load(attr_id)

    assert attr_C == attr_D

    with pytest.raises(IOError) as err_info:
        kwargs = {"attr": attr_C, "attr_id": attr_id, "write_mode": "a-"}
        h5pywrappers.attr.save(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"attr": attr_C, "attr_id": attr_id, "write_mode": "w"}
        h5pywrappers.attr.save(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"attr": attr_C, "attr_id": attr_id, "write_mode": "w-"}
        h5pywrappers.attr.save(**kwargs)

    filename = obj_id.core_attrs["filename"]
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



###########################
## Define error messages ##
###########################
