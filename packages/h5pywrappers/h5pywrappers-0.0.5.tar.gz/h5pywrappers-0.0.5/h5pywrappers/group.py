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
r"""For loading and saving HDF5 groups.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For checking whether a file exists at a given path.
import pathlib

# For removing directories.
import shutil



# For saving HDF5 groups and checking whether an object is an HDF5 group.
import h5py

# For validating objects.
import czekitout.check



# For loading and pre-saving HDF5 objects.
import h5pywrappers.obj

# For reusing validation and conversions functions.
import h5pywrappers.dataset



##################################
## Define classes and functions ##
##################################

# List of public objects in objects.
__all__ = ["load",
           "save"]



def _check_and_convert_group_id(params):
    obj_name = "group_id"
    obj = params[obj_name]
    
    accepted_types = (h5pywrappers.obj.ID,)

    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_types": accepted_types}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)
    group_id = obj

    return group_id



def _check_and_convert_read_only(params):
    module_alias = h5pywrappers.obj
    func_alias = module_alias._check_and_convert_read_only
    read_only = func_alias(params)

    return read_only



_module_alias = h5pywrappers.obj
_default_read_only = _module_alias._default_read_only



def load(group_id, read_only=_default_read_only):
    r"""Load an HDF5 group from an HDF5 file.

    Note that users can access the HDF5 file object to which the HDF5 group of
    interest belongs via ``group.file``, where ``group`` is the HDF5 group of
    interest. To close the HDF5 file, users can run the command
    ``group.file.close()``, however by doing so, any other HDF5 objects
    belonging to that file will become unusable.

    Parameters
    ----------
    group_id : :class:`h5pywrappers.obj.ID`
        The parameter set specifying the HDF5 group of interest.
    read_only : `bool`, optional
        If ``read_only`` is set to ``True``, then the HDF5 group of interest
        cannot be modified after loading it. Otherwise, if ``read_only`` is set
        to ``False``, then the HDF5 group of interest can be modified after
        loading it.

    Returns
    -------
    group : :class:`h5py.Group`
        The HDF5 group of interest.

    """
    params = locals()
    global_symbol_table = globals()
    for param_name in params:
        func_name = "_check_and_convert_" + param_name
        func_alias = global_symbol_table[func_name]
        params[param_name] = func_alias(params)

    kwargs = params
    group = _load(**kwargs)

    return group



def _load(group_id, read_only):
    kwargs = {"obj_id": group_id, "read_only": read_only}
    group = h5pywrappers.obj.load(**kwargs)
    
    try:
        accepted_types = (h5py._hl.group.Group,)
        kwargs = {"obj": group,
                  "obj_name": "group",
                  "accepted_types": accepted_types}
        czekitout.check.if_instance_of_any_accepted_types(**kwargs)
    except BaseException as err:
        group.file.close()
        raise err

    return group



def _check_and_convert_group(params):
    obj_name = "group"
    obj = params[obj_name]
    
    accepted_types = (h5py._hl.group.Group, type(None))

    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_types": accepted_types}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)
    group = obj

    return group



def _check_and_convert_write_mode(params):
    module_alias = h5pywrappers.dataset
    func_alias = module_alias._check_and_convert_write_mode
    write_mode = func_alias(params)

    return write_mode



_module_alias = h5pywrappers.dataset
_default_write_mode = _module_alias._default_write_mode



def save(group, group_id, write_mode=_default_write_mode):
    r"""Save an HDF5 group to an HDF5 file.

    Parameters
    ----------
    group : :class:`h5py.Group` | `None`
        The HDF5 group of interest to save to an HDF5 file. If ``group`` is set
        to `None`, then an empty HDF5 group is to be saved.
    group_id : :class:`h5pywrappers.obj.ID`
        The parameter set specifying where to save the HDF5 group of interest.
    write_mode : "w" | "w-" | "a" | "a-", optional
        The write mode upon opening the HDF5 file to which to save the HDF5
        group of interest: if ``write_mode`` is set to ``"w"``, then the target
        HDF5 file is emptied prior to saving the HDF5 group of interest; else if
        ``write_mode`` is set to ``"w-"``, then the HDF5 group of interest is
        saved unless a file already exists with the target filename, in which
        case an error is raised and the target HDF5 file is left unmodified;
        else if ``write_mode`` is set to ``"a-"``, then the HDF5 group of
        interest is saved unless an HDF5 object already exists at the target
        HDF5 path of the target HDF5 file, in which case an error is raised and
        the target HDF5 file is left unmodified; else if ``write_mode`` is set
        to ``"a"``, then the HDF5 group of interest is saved without emptying
        the target HDF5 file, replacing any HDF5 object at the target HDF5 path
        should one exist prior to saving.

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
    _save(**kwargs)

    return None



def _save(group, group_id, write_mode):
    group, write_mode = _pre_save(group, group_id, write_mode)

    group_id_core_attrs = group_id.get_core_attrs(deep_copy=False)
    filename = group_id_core_attrs["filename"]
    path_in_file = group_id_core_attrs["path_in_file"]

    with h5py.File(filename, "a") as file_obj:
        if path_in_file not in file_obj:
            if group is None:
                file_obj.create_group(path_in_file)
            else:
                file_obj.copy(group, path_in_file)

    return None



def _pre_save(group, group_id, write_mode):
    h5pywrappers.obj._pre_save(group_id)

    filename = group_id.core_attrs["filename"]
    path_in_file = group_id.core_attrs["path_in_file"]
    first_new_dir_made = h5pywrappers.obj._mk_parent_dir(filename)

    file_already_exists = pathlib.Path(filename).is_file()

    current_func_name = "_pre_save"

    if write_mode in ("w", "w-"):
        if write_mode == "w-":
            if file_already_exists:
                key = current_func_name+"_err_msg_1"
                unformatted_err_msg = globals()[key]
                err_msg = unformatted_err_msg.format(path_in_file, filename)
                raise IOError(err_msg)
        with h5py.File(filename, "w") as file_obj:
            pass
        file_is_not_new = False
    else:
        file_is_not_new = file_already_exists

    with h5py.File(filename, "a") as file_obj:        
        if path_in_file in file_obj:
            if (write_mode == "a-") and file_is_not_new:
                key = current_func_name+"_err_msg_2"
                unformatted_err_msg = globals()[key]
                err_msg = unformatted_err_msg.format(path_in_file, filename)
                raise IOError(err_msg)
            if file_is_not_new:
                del file_obj[path_in_file]

    return group, write_mode



###########################
## Define error messages ##
###########################

_pre_save_err_msg_1 = \
    ("Cannot save the HDF5 group to the HDF5 path ``'{}'`` of the HDF5 file at "
     "the file path ``'{}'`` because an HDF5 file already exists at said file "
     "path and the parameter ``write_mode`` was set to ``'w-'``, which "
     "prohibits modifying any such pre-existing file.")
_pre_save_err_msg_2 = \
    ("Cannot save the HDF5 group to the HDF5 path ``'{}'`` of the HDF5 file at "
     "the file path ``'{}'`` because an HDF5 object already exists there and "
     "the parameter ``write_mode`` was set to ``'a-'``, which prohibits "
     "replacing any such pre-existing HDF5 object.")
