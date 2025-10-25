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
r"""For identifying and loading HDF5 objects.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For performing deep copies.
import copy

# For checking whether a file exists at a given path, making directories, and
# for removing files.
import pathlib

# For removing directories.
import shutil



# For loading HDF5 files.
import h5py

# For validating and converting objects.
import czekitout.check
import czekitout.convert

# For defining classes that support enforced validation, updatability,
# pre-serialization, and de-serialization.
import fancytypes



##################################
## Define classes and functions ##
##################################

# List of public objects in objects.
__all__ = ["ID",
           "load"]



def _check_and_convert_filename(params):
    obj_name = "filename"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    filename = czekitout.convert.to_str_from_str_like(**kwargs)

    return filename



def _pre_serialize_filename(filename):
    obj_to_pre_serialize = filename
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_filename(serializable_rep):
    filename = serializable_rep

    return filename



def _check_and_convert_path_in_file(params):
    obj_name = "path_in_file"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    path_in_file = czekitout.convert.to_str_from_str_like(**kwargs)

    current_func_name = "_check_and_convert_path_in_file"

    if len(path_in_file) == 0:
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise ValueError(err_msg)

    return path_in_file



def _pre_serialize_path_in_file(path_in_file):
    obj_to_pre_serialize = path_in_file
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_path_in_file(serializable_rep):
    path_in_file = serializable_rep

    return path_in_file



_default_skip_validation_and_conversion = False



class ID(fancytypes.PreSerializableAndUpdatable):
    r"""A parameter set specifying an HDF5 object in an HDF5 file or an HDF5 
    file to be.

    Parameters
    ----------
    filename : `str`
        The relative or absolute filename of the HDF5 file that contains the
        HDF5 object of interest.
    path_in_file : `str`
        The HDF5 path to the HDF5 object of interest contained in the HDF5 file
        specified by ``filename``.
    skip_validation_and_conversion : `bool`, optional
        Let ``validation_and_conversion_funcs`` and ``core_attrs`` denote the
        attributes :attr:`~fancytypes.Checkable.validation_and_conversion_funcs`
        and :attr:`~fancytypes.Checkable.core_attrs` respectively, both of which
        being `dict` objects.

        Let ``params_to_be_mapped_to_core_attrs`` denote the `dict`
        representation of the constructor parameters excluding the parameter
        ``skip_validation_and_conversion``, where each `dict` key ``key`` is a
        different constructor parameter name, excluding the name
        ``"skip_validation_and_conversion"``, and
        ``params_to_be_mapped_to_core_attrs[key]`` would yield the value of the
        constructor parameter with the name given by ``key``.

        If ``skip_validation_and_conversion`` is set to ``False``, then for each
        key ``key`` in ``params_to_be_mapped_to_core_attrs``,
        ``core_attrs[key]`` is set to ``validation_and_conversion_funcs[key]
        (params_to_be_mapped_to_core_attrs)``.

        Otherwise, if ``skip_validation_and_conversion`` is set to ``True``,
        then ``core_attrs`` is set to
        ``params_to_be_mapped_to_core_attrs.copy()``. This option is desired
        primarily when the user wants to avoid potentially expensive deep copies
        and/or conversions of the `dict` values of
        ``params_to_be_mapped_to_core_attrs``, as it is guaranteed that no
        copies or conversions are made in this case.

    """
    ctor_param_names = ("filename", "path_in_file")
    kwargs = {"namespace_as_dict": globals(),
              "ctor_param_names": ctor_param_names}
    
    _validation_and_conversion_funcs_ = \
        fancytypes.return_validation_and_conversion_funcs(**kwargs)
    _pre_serialization_funcs_ = \
        fancytypes.return_pre_serialization_funcs(**kwargs)
    _de_pre_serialization_funcs_ = \
        fancytypes.return_de_pre_serialization_funcs(**kwargs)

    del ctor_param_names, kwargs

    

    def __init__(self,
                 filename,
                 path_in_file,
                 skip_validation_and_conversion=\
                 _default_skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        kwargs = ctor_params
        kwargs["skip_cls_tests"] = True
        fancytypes.PreSerializableAndUpdatable.__init__(self, **kwargs)

        return None



    @classmethod
    def get_validation_and_conversion_funcs(cls):
        validation_and_conversion_funcs = \
            cls._validation_and_conversion_funcs_.copy()

        return validation_and_conversion_funcs


    
    @classmethod
    def get_pre_serialization_funcs(cls):
        pre_serialization_funcs = \
            cls._pre_serialization_funcs_.copy()

        return pre_serialization_funcs


    
    @classmethod
    def get_de_pre_serialization_funcs(cls):
        de_pre_serialization_funcs = \
            cls._de_pre_serialization_funcs_.copy()

        return de_pre_serialization_funcs



def _check_and_convert_obj_id(params):
    param_name = "obj_id"
    name_of_obj_alias_of_obj_id = params.get("name_of_obj_alias_of_"+param_name,
                                             param_name)

    obj_name = param_name
    obj = copy.deepcopy(params[obj_name])
    
    accepted_types = (ID,)

    kwargs = {"obj": obj,
              "obj_name": name_of_obj_alias_of_obj_id,
              "accepted_types": accepted_types}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)
    obj_id = obj

    return obj_id



def _pre_serialize_obj_id(obj_id):
    obj_to_pre_serialize = obj_id
    serializable_rep = obj_to_pre_serialize.pre_serialize()
    
    return serializable_rep



def _de_pre_serialize_obj_id(serializable_rep):
    kwargs = {"serializable_rep": serializable_rep,
              "skip_validation_and_conversion": True}
    obj_id = ID.de_pre_serialize(**kwargs)

    return obj_id



def _check_and_convert_read_only(params):
    obj_name = "read_only"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    read_only = czekitout.convert.to_bool(**kwargs)

    return read_only



_default_read_only = True



def load(obj_id, read_only=_default_read_only):
    r"""Load an HDF5 object from an HDF5 file.

    Note that users can access the HDF5 file object to which the HDF5 object of
    interest belongs via ``obj.file``, where ``obj`` is the HDF5 object of
    interest. To close the HDF5 file, users can run the command
    ``obj.file.close()``, however by doing so, any other HDF5 objects belonging
    to that file will become unusable.

    Parameters
    ----------
    obj_id : :class:`h5pywrappers.obj.ID`
        The parameter set specifying the HDF5 object of interest.
    read_only : `bool`, optional
        If ``read_only`` is set to ``True``, then the HDF5 object of interest
        cannot be modified after loading it. Otherwise, if ``read_only`` is set
        to ``False``, then the HDF5 object of interest can be modified after
        loading it.

    Returns
    -------
    obj : :class:`h5py.Group` | :class:`h5py.Dataset`
        The HDF5 object of interest.

    """
    params = locals()
    global_symbol_table = globals()
    for param_name in params:
        func_name = "_check_and_convert_" + param_name
        func_alias = global_symbol_table[func_name]
        params[param_name] = func_alias(params)

    kwargs = params
    obj = _load(**kwargs)

    return obj



def _load(obj_id, read_only):
    read_only = _pre_load(obj_id, read_only)

    obj_id_core_attrs = obj_id.get_core_attrs(deep_copy=False)
    filename = obj_id_core_attrs["filename"]
    path_in_file = obj_id_core_attrs["path_in_file"]

    if read_only:
        file_obj = h5py.File(filename, "r")
    else:
        file_obj = h5py.File(filename, "a")
        
    obj = file_obj[path_in_file]

    return obj



def _pre_load(obj_id, read_only):
    obj_id_core_attrs = obj_id.get_core_attrs(deep_copy=False)
    filename = obj_id_core_attrs["filename"]
    path_in_file = obj_id_core_attrs["path_in_file"]

    file_mode = "r" if read_only else "a"

    current_func_name = "_pre_load"

    try:
        if not pathlib.Path(filename).is_file():
            raise FileNotFoundError
        with h5py.File(filename, file_mode) as file_obj:
            pass
    except FileNotFoundError:
        err_msg = globals()[current_func_name+"_err_msg_1"].format(filename)
        raise FileNotFoundError(err_msg)
    except PermissionError:
        err_msg = globals()[current_func_name+"_err_msg_2"].format(filename)
        raise PermissionError(err_msg)
    except OSError as err:
        if "file signature not found" in str(err):
            err_msg = globals()[current_func_name+"_err_msg_3"].format(filename)
        else:
            err_msg = globals()[current_func_name+"_err_msg_4"].format(filename)
        raise OSError(err_msg)

    with h5py.File(filename, file_mode) as file_obj:
        if path_in_file not in file_obj:
            unformatted_err_msg = globals()[current_func_name+"_err_msg_5"]
            err_msg = unformatted_err_msg.format(path_in_file, filename)
            raise ValueError(err_msg)

    return read_only



def _pre_save(obj_id):
    obj_id_core_attrs = obj_id.get_core_attrs(deep_copy=False)
    filename = obj_id_core_attrs["filename"]
    path_in_file = obj_id.core_attrs["path_in_file"]

    first_new_dir_made = _mk_parent_dir(filename)

    current_func_name = "_pre_save"

    try:
        file_does_not_exist = (not pathlib.Path(filename).is_file())
    except PermissionError:
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(filename)
        raise PermissionError(err_msg)
            
    if file_does_not_exist:
        try:
            with h5py.File(filename, "w") as file_obj:
                pass
        except PermissionError:
            unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
            err_msg = unformatted_err_msg.format(filename)
            raise PermissionError(err_msg)
        
        pathlib.Path(filename).unlink()
    else:
        try:
            with h5py.File(filename, "a") as file_obj:
                pass
        except PermissionError:
            unformatted_err_msg = globals()[current_func_name+"_err_msg_2"]
            err_msg = unformatted_err_msg.format(filename)
            raise PermissionError(err_msg)
        except OSError as err:
            key = (current_func_name + "_err_msg_3"
                   if ("file signature not found" in str(err))
                   else current_func_name + "_err_msg_4")                    
            err_msg = globals()[key].format(filename)
            raise OSError(err_msg)
        
    _check_for_intermediary_datasets_along_path_in_file(obj_id)

    if first_new_dir_made is not None:
        shutil.rmtree(first_new_dir_made)

    return None



def _mk_parent_dir(filename):
    current_func_name = "_mk_parent_dir"

    try:
        parent_dir_path = pathlib.Path(filename).resolve().parent
        temp_dir_path = pathlib.Path(parent_dir_path.root)

        parent_dir_did_not_already_exist = False

        for path_part in parent_dir_path.parts[1:]:
            temp_dir_path = pathlib.Path.joinpath(temp_dir_path, path_part)
            if not temp_dir_path.is_dir():
                parent_dir_did_not_already_exist = True
                break

        pathlib.Path(parent_dir_path).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        err_msg = globals()[current_func_name+"_err_msg_1"].format(filename)
        raise PermissionError(err_msg)

    first_new_dir_made = (temp_dir_path
                          if parent_dir_did_not_already_exist
                          else None)

    return first_new_dir_made



def _check_for_intermediary_datasets_along_path_in_file(obj_id):
    obj_id_core_attrs = obj_id.get_core_attrs(deep_copy=False)
    filename = obj_id_core_attrs["filename"]
    path_in_file = obj_id.core_attrs["path_in_file"]

    file_is_not_new = pathlib.Path(filename).is_file()

    current_func_name = "_check_for_intermediary_datasets_along_path_in_file"

    if file_is_not_new:
        with h5py.File(filename, "a") as file_obj:
            if path_in_file not in file_obj:
                path_in_file = pathlib.Path(path_in_file)
                num_parents = len(path_in_file.parents)
                for parent_idx in range(-1, -num_parents-1, -1):
                    path = str(path_in_file.parents[num_parents+parent_idx])
                    if path in file_obj:
                        if isinstance(file_obj[path], h5py._hl.dataset.Dataset):
                            key = current_func_name + "_err_msg_1"
                            unformatted_err_msg = globals()[key]
                            err_msg = unformatted_err_msg.format(path_in_file,
                                                                 path,
                                                                 filename)
                            raise ValueError(err_msg)
                    else:
                        break

    return None



###########################
## Define error messages ##
###########################

_check_and_convert_path_in_file_err_msg_1 = \
    ("The object ``path_in_file`` must be a non-empty string.")

_pre_load_err_msg_1 = \
    ("No file exists at the file path ``'{}'``.")
_pre_load_err_msg_2 = \
    ("Cannot access the file path ``'{}'`` because of insufficient "
     "permissions.")
_pre_load_err_msg_3 = \
    ("No HDF5 file exists at the file path ``'{}'``.")
_pre_load_err_msg_4 = \
    ("Unable to synchronously open the HDF5 file at the file path ``'{}'``: "
     "see traceback for details.")
_pre_load_err_msg_5 = \
    ("No HDF5 object was found at the HDF5 path ``'{}'`` of the HDF5 file "
     "at the file path ``'{}'``.")

_pre_save_err_msg_1 = \
    _pre_load_err_msg_2
_pre_save_err_msg_2 = \
    ("Cannot write to the file at the file path ``'{}'`` because of "
     "insufficient permissions.")
_pre_save_err_msg_3 = \
    _pre_load_err_msg_3
_pre_save_err_msg_4 = \
    _pre_load_err_msg_4

_mk_parent_dir_err_msg_1 = \
    _pre_load_err_msg_2

_check_for_intermediary_datasets_along_path_in_file_err_msg_1 = \
    ("The object ``path_in_file``, which stores the string ``'{}'``, does not "
     "specify a valid HDF5 path: there is an HDF5 dataset at the intermediate "
     "path ``'{}'`` of the HDF5 file ``'{}'``.")
