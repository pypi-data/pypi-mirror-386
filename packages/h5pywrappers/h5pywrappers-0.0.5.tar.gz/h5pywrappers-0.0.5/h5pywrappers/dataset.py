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
r"""For loading and saving HDF5 datasets.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For checking whether a file exists at a given path.
import pathlib



# For saving HDF5 datasets and checking whether an object is an HDF5 dataset.
import h5py

# For checking whether an object is a numpy array.
import numpy as np

# For type-checking, validating, and converting objects.
import czekitout.check
import czekitout.convert

# For defining classes that support enforced validation, updatability,
# pre-serialization, and de-serialization.
import fancytypes



# For loading and pre-saving HDF5 objects.
import h5pywrappers.obj



##################################
## Define classes and functions ##
##################################

# List of public objects in objects.
__all__ = ["load",
           "save"]



def _check_and_convert_dataset_id(params):
    obj_name = "dataset_id"

    param_name_1 = "obj_id"
    param_name_2 = "name_of_obj_alias_of_"+param_name_1
    params = params.copy()
    params[param_name_2] = obj_name
    params[param_name_1] = params[params[param_name_2]]

    module_alias = h5pywrappers.obj
    func_alias = module_alias._check_and_convert_obj_id
    dataset_id = func_alias(params)

    return dataset_id



def _pre_serialize_dataset_id(dataset_id):
    obj_to_pre_serialize = dataset_id

    param_name = "obj_id"

    module_alias = h5pywrappers.obj
    func_alias = module_alias._pre_serialize_obj_id
    kwargs = {param_name: obj_to_pre_serialize}
    serializable_rep = func_alias(**kwargs)
    
    return serializable_rep



def _de_pre_serialize_dataset_id(serializable_rep):
    module_alias = h5pywrappers.obj
    func_alias = module_alias._de_pre_serialize_obj_id
    dataset_id = func_alias(serializable_rep)

    return dataset_id



def _check_and_convert_read_only(params):
    module_alias = h5pywrappers.obj
    func_alias = module_alias._check_and_convert_read_only
    read_only = func_alias(params)

    return read_only



_module_alias = h5pywrappers.obj
_default_read_only = _module_alias._default_read_only



def load(dataset_id, read_only=_default_read_only):
    r"""Load an HDF5 dataset from an HDF5 file.

    Note that users can access the HDF5 file object to which the HDF5 dataset of
    interest belongs via ``dataset.file``, where ``dataset`` is the HDF5 dataset
    of interest. To close the HDF5 file, users can run the command
    ``dataset.file.close()``, however by doing so, any other HDF5 objects
    belonging to that file will become unusable.

    Parameters
    ----------
    dataset_id : :class:`h5pywrappers.obj.ID`
        The parameter set specifying the HDF5 dataset of interest.
    read_only : `bool`, optional
        If ``read_only`` is set to ``True``, then the HDF5 dataset of interest
        cannot be modified after loading it. Otherwise, if ``read_only`` is set
        to ``False``, then the HDF5 dataset of interest can be modified after
        loading it.

    Returns
    -------
    dataset : :class:`h5py.Dataset`
        The HDF5 dataset of interest.

    """
    params = locals()
    global_symbol_table = globals()
    for param_name in params:
        func_name = "_check_and_convert_" + param_name
        func_alias = global_symbol_table[func_name]
        params[param_name] = func_alias(params)

    kwargs = params
    dataset = _load(**kwargs)

    return dataset



def _load(dataset_id, read_only):
    kwargs = {"obj_id": dataset_id, "read_only": read_only}
    dataset = h5pywrappers.obj.load(**kwargs)

    current_func_name = "_load"
    
    accepted_types = (h5py._hl.dataset.Dataset,)
    kwargs = {"obj": dataset,
              "obj_name": "dataset",
              "accepted_types": accepted_types}    
    try:
        czekitout.check.if_instance_of_any_accepted_types(**kwargs)
    except:
        dataset.file.close()
        
        dataset_id_core_attrs = dataset_id.get_core_attrs(deep_copy=False)
        filename = dataset_id_core_attrs["filename"]
        path_in_file = dataset_id_core_attrs["path_in_file"]

        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(path_in_file, filename)
        raise TypeError(err_msg)

    return dataset



def _check_and_convert_dataset(params):
    param_name = \
        "dataset"
    name_of_obj_alias_of_dataset = \
        params.get("name_of_obj_alias_of_"+param_name, param_name)

    obj_name = "dataset"
    obj = params[obj_name]

    current_func_name = "_check_and_convert_dataset"
    
    if not isinstance(obj, (h5py._hl.dataset.Dataset, str)):
        try:
            kwargs = {"obj": obj, "obj_name": name_of_obj_alias_of_dataset}
            dataset = czekitout.convert.to_numpy_array(**kwargs)
        except:
            err_msg = globals()[current_func_name+"_err_msg_1"]
            raise TypeError(err_msg)
    else:
        dataset = obj

    return dataset



def _check_and_convert_write_mode(params):
    obj_name = "write_mode"
    obj = params[obj_name]

    func_alias = czekitout.check.if_one_of_any_accepted_strings
    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_strings": ("w", "w-", "a", "a-")}
    func_alias(**kwargs)

    kwargs = {"obj": obj, "obj_name": obj_name}
    write_mode = czekitout.convert.to_str_from_str_like(**kwargs)

    return write_mode



_default_write_mode = "w-"



def save(dataset, dataset_id, write_mode=_default_write_mode):
    r"""Save an HDF5 dataset to an HDF5 file.

    Parameters
    ----------
    dataset : :class:`h5py.Dataset` | `array_like` | `str`
        The HDF5 dataset of interest to save to an HDF5 file.
    dataset_id : :class:`h5pywrappers.obj.ID`
        The parameter set specifying where to save the HDF5 dataset of interest.
    write_mode : "w" | "w-" | "a" | "a-", optional
        The write mode upon opening the HDF5 file to which to save the HDF5
        dataset of interest: if ``write_mode`` is set to ``"w"``, then the
        target HDF5 file is emptied prior to saving the HDF5 dataset of
        interest; else if ``write_mode`` is set to ``"w-"``, then the HDF5
        dataset of interest is saved unless a file already exists with the
        target filename, in which case an error is raised and the target HDF5
        file is left unmodified; else if ``write_mode`` is set to ``"a-"``, then
        the HDF5 dataset of interest is saved unless an HDF5 object already
        exists at the target HDF5 path of the target HDF5 file, in which case an
        error is raised and the target HDF5 file is left unmodified; else if
        ``write_mode`` is set to ``"a"``, then the HDF5 dataset of interest is
        saved without emptying the target HDF5 file, replacing any HDF5 object
        at the target HDF5 path should one exist prior to saving.

    Returns
    -------

    """
    params = locals()
    global_symbol_table = globals()
    for param_name in params:
        func_name = "_check_and_convert_" + param_name
        func_alias = global_symbol_table[func_name]
        params[param_name] = func_alias(params)

    kwargs = params
    obj = _save(**kwargs)

    return None



def _save(dataset, dataset_id, write_mode):
    _pre_save(dataset, dataset_id, write_mode)

    dataset_id_core_attrs = dataset_id.get_core_attrs(deep_copy=False)
    filename = dataset_id_core_attrs["filename"]
    path_in_file = dataset_id_core_attrs["path_in_file"]

    with h5py.File(filename, "a") as file_obj:
        if isinstance(dataset, (np.ndarray, str)):
            file_obj.create_dataset(path_in_file, data=dataset)
        else:
            file_obj.copy(dataset, path_in_file)

    return None



def _pre_save(dataset, dataset_id, write_mode):
    h5pywrappers.obj._pre_save(dataset_id)

    dataset_id_core_attrs = dataset_id.get_core_attrs(deep_copy=False)
    filename = dataset_id_core_attrs["filename"]
    path_in_file = dataset_id_core_attrs["path_in_file"]
    
    first_new_dir_made = h5pywrappers.obj._mk_parent_dir(filename)

    current_func_name = "_pre_save"

    if write_mode in ("w", "w-"):
        if write_mode == "w-":
            if pathlib.Path(filename).is_file():
                unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
                err_msg = unformatted_err_msg.format(path_in_file, filename)
                raise IOError(err_msg)
        with h5py.File(filename, "w") as file_obj:
            pass
        
    with h5py.File(filename, "a") as file_obj:
        if path_in_file in file_obj:
            if write_mode == "a-":
                unformatted_err_msg = globals()[current_func_name+"_err_msg_2"]
                err_msg = unformatted_err_msg.format(path_in_file, filename)
                raise IOError(err_msg)
            del file_obj[path_in_file]

    return None



###########################
## Define error messages ##
###########################

_load_err_msg_1 = \
    ("The HDF5 object at the HDF5 path ``'{}'`` of the HDF5 file at the file "
     "path ``'{}'`` must be an HDF5 dataset.")

_check_and_convert_dataset_err_msg_1 = \
    ("The object ``dataset`` must be array-like, an HDF5 dataset, or a string.")

_pre_save_err_msg_1 = \
    ("Cannot save the dataset to the HDF5 path ``'{}'`` of the HDF5 file at "
     "the file path ``'{}'`` because an HDF5 file already exists at said file "
     "path and the parameter ``write_mode`` was set to ``'w-'``, which "
     "prohibits modifying any such pre-existing file.")
_pre_save_err_msg_2 = \
    ("Cannot save the dataset to the HDF5 path ``'{}'`` of the HDF5 file at "
     "the file path ``'{}'`` because an HDF5 object already exists there and "
     "the parameter ``write_mode`` was set to ``'a-'``, which prohibits "
     "replacing any such pre-existing HDF5 object.")
