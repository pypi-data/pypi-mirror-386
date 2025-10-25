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
r"""Contains tests for the module :mod:`h5pywrappers.group`.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For removing files.
import pathlib

# For removing directories.
import shutil

# For setting file permissions.
import os



# For general array handling.
import numpy as np

# For operations related to unit tests.
import pytest



# For loading and saving HDF5 objects.
import h5pywrappers.obj

# For loading and saving HDF5 datasets.
import h5pywrappers.dataset

# For loading and saving HDF5 groups.
import h5pywrappers.group



##################################
## Define classes and functions ##
##################################



@pytest.fixture
def dataset_id():
    fixture_output = h5pywrappers.obj.ID(filename="./test_data/test_file_1.h5",
                                         path_in_file="/group_1/dataset_1")

    return fixture_output



def test_1_of_save(dataset_id):
    kwargs = {"dataset": np.arange(10),
              "dataset_id": dataset_id,
              "write_mode": "w"}
    h5pywrappers.dataset.save(**kwargs)

    filename = dataset_id.core_attrs["filename"]
    path_to_group = "/group_1"
    kwargs = {"filename": filename, "path_in_file": path_to_group}
    group_id = h5pywrappers.obj.ID(**kwargs)
    
    kwargs = {"group_id": group_id, "read_only": True}
    group = h5pywrappers.group.load(**kwargs)

    group_candidates = (None, group, ((1,), (2, 3)))
    
    for group_candidate in group_candidates:
        group_id = h5pywrappers.obj.ID(filename="./test_data/test_file_2.h5",
                                       path_in_file=path_to_group)

        kwargs = {"group": group_candidate,
                  "group_id": group_id,
                  "write_mode": "w"}
        if isinstance(group_candidate, tuple):
            with pytest.raises(TypeError) as err_info:
                h5pywrappers.group.save(**kwargs)
        else:
            h5pywrappers.group.save(**kwargs)

    group.file.close()
    shutil.rmtree(pathlib.Path(filename).parent)

    kwargs = {"group": None, "group_id": group_id}
    for iteration_idx in range(4):
        kwargs["write_mode"] = ("w-", "w-", "a", "a-")[iteration_idx]
        if (iteration_idx%2) == 0:
            h5pywrappers.group.save(**kwargs)
        else:
            with pytest.raises(IOError) as err_info:
                h5pywrappers.group.save(**kwargs)

    shutil.rmtree(pathlib.Path(filename).parent)

    return None



def test_2_of_save(dataset_id):
    with pytest.raises(ValueError) as err_info:
        filename = dataset_id.core_attrs["filename"]
        path_to_group = ""
        kwargs = {"filename": filename, "path_in_file": path_to_group}
        group_id = h5pywrappers.obj.ID(**kwargs)

    path_to_group = "/"
    kwargs = {"filename": filename, "path_in_file": path_to_group}
    group_id = h5pywrappers.obj.ID(**kwargs)

    kwargs = {"group": None, "group_id": group_id, "write_mode": "a-"}
    h5pywrappers.group.save(**kwargs)

    with pytest.raises(IOError) as err_info:
        h5pywrappers.group.save(**kwargs)

    dirname = str(pathlib.Path(filename).parent)
    os.chmod(dirname, 0o111)

    filename = dirname + "/foo/bar.h5"
    new_core_attr_subset_candidate = {"filename": filename}
    group_id.update(new_core_attr_subset_candidate)

    with pytest.raises(PermissionError) as err_info:
        h5pywrappers.group.save(**kwargs)

    os.chmod(dirname, 0o711)

    filename = dirname + "/non_h5_file"
    with open(filename, "w") as file_obj:
        file_obj.write("text")

    path_to_group = "/group_1"
    kwargs = {"filename": filename, "path_in_file": path_to_group}
    group_id = h5pywrappers.obj.ID(**kwargs)

    with pytest.raises(OSError) as err_info:
        kwargs = {"group": None, "group_id": group_id, "write_mode": "a"}
        h5pywrappers.group.save(**kwargs)

    shutil.rmtree(dirname)
            
    return None



def test_3_of_save(dataset_id):
    kwargs = {"dataset": np.arange(10),
              "dataset_id": dataset_id,
              "write_mode": "w"}
    h5pywrappers.dataset.save(**kwargs)

    filename = dataset_id.core_attrs["filename"]
    path_to_group = dataset_id.core_attrs["path_in_file"] + "/group_2"
    kwargs = {"filename": filename, "path_in_file": path_to_group}
    group_id = h5pywrappers.obj.ID(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"group": None, "group_id": group_id, "write_mode": "a"}
        h5pywrappers.group.save(**kwargs)

    path_to_group = "/group_1/group_2/group_3"
    new_core_attr_subset_candidate = {"path_in_file": path_to_group}
    group_id.update(new_core_attr_subset_candidate)

    kwargs = {"group": None, "group_id": group_id, "write_mode": "a"}
    h5pywrappers.group.save(**kwargs)

    pathlib.Path(filename).unlink()

    dirname = str(pathlib.Path(filename).parent)
    os.chmod(dirname, 0o111)

    with pytest.raises(PermissionError) as err_info:
        kwargs = {"group": None, "group_id": group_id, "write_mode": "w"}
        h5pywrappers.group.save(**kwargs)

    os.chmod(dirname, 0o711)

    h5pywrappers.group.save(**kwargs)

    os.chmod(filename, 0o111)

    with pytest.raises(PermissionError) as err_info:
        kwargs = {"group": None, "group_id": group_id, "write_mode": "a"}
        h5pywrappers.group.save(**kwargs)

    os.chmod(filename, 0o711)
    
    shutil.rmtree(pathlib.Path(filename).parent)
            
    return None



def test_4_of_save(dataset_id):
    kwargs = {"dataset": np.arange(10),
              "dataset_id": dataset_id,
              "write_mode": "w"}
    h5pywrappers.dataset.save(**kwargs)

    filename = dataset_id.core_attrs["filename"]
    path_to_group = "/group_1"
    kwargs = {"filename": filename, "path_in_file": path_to_group}
    group_id = h5pywrappers.obj.ID(**kwargs)

    kwargs = {"group_id": group_id, "read_only": True}
    group = h5pywrappers.group.load(**kwargs)

    with pytest.raises(OSError) as err_info:
        kwargs = {"group": None, "group_id": group_id, "write_mode": "a"}
        h5pywrappers.group.save(**kwargs)

    dirname = str(pathlib.Path(filename).parent) + "/another_dir"
    pathlib.Path(dirname).mkdir(parents=True, exist_ok=True)

    os.chmod(dirname, 0o111)

    filename = dirname + "/test_file_3.h5"
    new_core_attr_subset_candidate = {"filename": filename}
    group_id.update(new_core_attr_subset_candidate)

    with pytest.raises(PermissionError) as err_info:
        kwargs = {"group": None, "group_id": group_id, "write_mode": "w"}
        h5pywrappers.group.save(**kwargs)

    os.chmod(dirname, 0o611)

    with pytest.raises(PermissionError) as err_info:
        kwargs = {"group": None, "group_id": group_id, "write_mode": "w"}
        h5pywrappers.group.save(**kwargs)

    filename = dataset_id.core_attrs["filename"]
    dirname = pathlib.Path(filename).parent
    shutil.rmtree(dirname)
            
    return None



def test_1_of_load(dataset_id):
    kwargs = {"dataset": np.arange(10),
              "dataset_id": dataset_id,
              "write_mode": "w"}
    h5pywrappers.dataset.save(**kwargs)

    filename = dataset_id.core_attrs["filename"]
    path_to_group = "/group_1"
    kwargs = {"filename": filename, "path_in_file": path_to_group}
    group_id = h5pywrappers.obj.ID(**kwargs)
    
    kwargs = {"group_id": group_id, "read_only": True}
    group = h5pywrappers.group.load(**kwargs)

    path_1 = pathlib.Path(group.name).resolve()
    path_2 = pathlib.Path(path_to_group).resolve()
    assert group.name == path_to_group

    path_1 = pathlib.Path(group.file.filename).resolve()
    path_2 = pathlib.Path(filename).resolve()
    assert path_1 == path_2

    group.file.close()

    with pytest.raises(TypeError) as err_info:
        kwargs = {"group_id": dataset_id, "read_only": True}
        h5pywrappers.group.load(**kwargs)

    pathlib.Path(filename).unlink()
        
    with pytest.raises(FileNotFoundError) as err_info:
        kwargs = {"group_id": group_id, "read_only": True}
        h5pywrappers.group.load(**kwargs)

    dirname = str(pathlib.Path(filename).parent)
    os.chmod(dirname, 0o611)

    with pytest.raises(PermissionError) as err_info:
        kwargs = {"group_id": dataset_id, "read_only": True}
        h5pywrappers.group.load(**kwargs)

    shutil.rmtree(dirname)
            
    return None



def test_2_of_load(dataset_id):
    kwargs = {"dataset": np.arange(10),
              "dataset_id": dataset_id,
              "write_mode": "w"}
    h5pywrappers.dataset.save(**kwargs)

    filename = dataset_id.core_attrs["filename"]    
    dirname = str(pathlib.Path(filename).parent)
    
    filename = dirname + "/non_h5_file"
    with open(filename, "w"):
        pass

    path_to_group = "/group_1"
    kwargs = {"filename": filename, "path_in_file": path_to_group}
    group_id = h5pywrappers.obj.ID(**kwargs)

    with pytest.raises(OSError) as err_info:
        kwargs = {"group_id": group_id, "read_only": True}
        h5pywrappers.group.load(**kwargs)

    filename = dataset_id.core_attrs["filename"]
    kwargs = {"filename": filename, "path_in_file": path_to_group}
    group_id = h5pywrappers.obj.ID(**kwargs)
    
    kwargs = {"group_id": group_id, "read_only": True}
    group = h5pywrappers.group.load(**kwargs)

    with pytest.raises(OSError) as err_info:
        kwargs = {"group_id": group_id, "read_only": False}
        h5pywrappers.group.load(**kwargs)

    group.file.close()

    path_to_group = "/invalid_path"
    kwargs = {"filename": filename, "path_in_file": path_to_group}
    group_id = h5pywrappers.obj.ID(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"group_id": group_id, "read_only": False}
        h5pywrappers.group.load(**kwargs)

    shutil.rmtree(dirname)
            
    return None



###########################
## Define error messages ##
###########################
