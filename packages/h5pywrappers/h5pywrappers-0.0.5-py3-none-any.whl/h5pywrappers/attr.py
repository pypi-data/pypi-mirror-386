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
r"""For loading and saving HDF5 object attributes.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For validating and converting objects.
import czekitout.check
import czekitout.convert

# For defining classes that support enforced validation, updatability,
# pre-serialization, and de-serialization.
import fancytypes



# For identifying HDF5 objects.
import h5pywrappers.obj



##################################
## Define classes and functions ##
##################################

# List of public objects in objects.
__all__ = ["ID",
           "load",
           "save"]



def _check_and_convert_obj_id(params):
    module_alias = h5pywrappers.obj
    func_alias = module_alias._check_and_convert_obj_id
    obj_id = func_alias(params)

    return obj_id



def _pre_serialize_obj_id(obj_id):
    obj_to_pre_serialize = obj_id

    param_name = "obj_id"

    module_alias = h5pywrappers.obj
    func_alias = module_alias._pre_serialize_obj_id
    kwargs = {param_name: obj_to_pre_serialize}
    serializable_rep = func_alias(**kwargs)
    
    return serializable_rep



def _de_pre_serialize_obj_id(serializable_rep):
    module_alias = h5pywrappers.obj
    func_alias = module_alias._de_pre_serialize_obj_id
    obj_id = func_alias(serializable_rep)

    return obj_id



def _check_and_convert_attr_name(params):
    obj_name = "attr_name"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    attr_name = czekitout.convert.to_str_from_str_like(**kwargs)

    return attr_name



def _pre_serialize_attr_name(attr_name):
    obj_to_pre_serialize = attr_name
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_attr_name(serializable_rep):
    attr_name = serializable_rep

    return attr_name



_module_alias = \
    h5pywrappers.obj
_default_skip_validation_and_conversion = \
    _module_alias._default_skip_validation_and_conversion



class ID(fancytypes.PreSerializableAndUpdatable):
    r"""A parameter set specifying an HDF5 attribute of an HDF5 object in an
    HDF5 file or an HDF5 file to be.

    Parameters
    ----------
    obj_id : :class:`h5pywrappers.obj.ID`
        The parameter set specifying the HDF5 object from which to load the
        HDF5 attribute of interest.
    attr_name : `str`
        The name of the HDF5 attribute of interest.
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
    ctor_param_names = ("obj_id", "attr_name")
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
                 obj_id,
                 attr_name,
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



def _check_and_convert_attr_id(params):
    obj_name = "attr_id"
    obj = params[obj_name]
    
    accepted_types = (ID,)

    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_types": accepted_types}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)
    attr_id = obj

    return attr_id



def load(attr_id):
    r"""Load an HDF5 attribute from an HDF5 file.

    Parameters
    ----------
    attr_id : :class:`h5pywrappers.attr.ID`
        The parameter set specifying the HDF5 attribute of interest.

    Returns
    -------
    attr : `any_type`
        The HDF5 attribute of interest.

    """
    params = locals()
    global_symbol_table = globals()
    for param_name in params:
        func_name = "_check_and_convert_" + param_name
        func_alias = global_symbol_table[func_name]
        params[param_name] = func_alias(params)

    kwargs = params
    attr = _load(**kwargs)

    return attr



def _load(attr_id):
    attr_id_core_attrs = attr_id.get_core_attrs(deep_copy=False)
    obj_id = attr_id_core_attrs["obj_id"]
    attr_name = attr_id_core_attrs["attr_name"]
    
    obj = h5pywrappers.obj.load(obj_id, read_only=True)

    current_func_name = "_load"

    try:
        attr = obj.attrs[attr_name]
        obj.file.close()
    except:
        obj.file.close()

        obj_id_core_attrs = obj_id.get_core_attrs(deep_copy=False)
        filename = obj_id_core_attrs["filename"]
        path_in_file = obj_id_core_attrs["path_in_file"]
        
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(path_in_file, filename, attr_name)
        raise ValueError(err_msg)

    return attr



def _check_and_convert_attr(params):
    obj_name = "attr"
    attr = params[obj_name]

    return attr



def _check_and_convert_write_mode(params):
    obj_name = "write_mode"
    obj = params[obj_name]

    func_alias = czekitout.check.if_one_of_any_accepted_strings
    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_strings": ("a", "a-")}
    func_alias(**kwargs)

    kwargs = {"obj": obj, "obj_name": obj_name}
    write_mode = czekitout.convert.to_str_from_str_like(**kwargs)

    return write_mode



_default_write_mode = "-a"



def save(attr, attr_id, write_mode=_default_write_mode):
    r"""Save an HDF5 attribute to an HDF5 file.

    Parameters
    ----------
    attr : `any_type`
        The HDF5 attribute of interest to save to an HDF5 file.
    attr_id : :class:`h5pywrappers.attr.ID`
        The parameter set specifying where to save the HDF5 attribute of 
        interest.
    write_mode : "a" | "a-", optional
        The write mode upon opening the HDF5 file to which to save the HDF5
        attribute of interest: if ``write_mode`` is set to ``"a-"``, then the
        HDF5 attribute of interest is saved without emptying the target HDF5
        file unless an HDF5 attribute with the same name as the target attribute
        name already exists at the target HDF5 path of the target HDF5 file, in
        which case an error is raised and the target HDF5 file is left
        unmodified; else if ``write_mode`` is set to ``"a"``, then the HDF5
        attribute of interest is saved without emptying the target HDF5 file,
        replacing any HDF5 object at the target HDF5 path should one exist prior
        to saving.

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



def _save(attr_id, write_mode, attr):
    attr_id_core_attrs = attr_id.get_core_attrs(deep_copy=False)
    obj_id = attr_id_core_attrs["obj_id"]
    attr_name = attr_id_core_attrs["attr_name"]
    
    h5pywrappers.obj._pre_save(obj_id)
    obj = h5pywrappers.obj.load(obj_id, read_only=False)

    current_func_name = "_save"

    if (write_mode == "a-") and (attr_name in obj.attrs):
        obj.file.close()

        obj_id_core_attrs = obj_id.get_core_attrs(deep_copy=False)
        filename = obj_id_core_attrs["filename"]
        path_in_file = obj_id_core_attrs["path_in_file"]

        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(attr_name, path_in_file, filename)
        raise IOError(err_msg)

    obj.attrs[attr_name] = attr
    obj.file.close()

    return None



###########################
## Define error messages ##
###########################

_load_err_msg_1 = \
    ("The HDF5 object located at the HDF5 path ``'{}'`` of the HDF5 file at "
     "the file path ``'{}'`` has no HDF5 attribute named ``'{}'``.")

_save_err_msg_1 = \
    ("Cannot save the HDF5 attribute named ``'{}'`` to an object at the HDF5 "
     "path ``'{}'`` of the HDF5 file at the file path ``'{}'`` because an HDF5 "
     "attribute of the same name already exists there and the parameter "
     "``write_mode`` was set to ``'a-'``, which prohibits replacing any such "
     "pre-existing HDF5 attribute.")
