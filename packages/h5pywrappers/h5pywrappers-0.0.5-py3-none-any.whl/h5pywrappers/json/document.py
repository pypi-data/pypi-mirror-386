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
r"""For loading and saving JSON documents objects.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For deserializing JSON documents.
import json



# For checking whether an object is an HDF5 object.
import h5py

# For validating objects.
import czekitout.check



# For loading and saving HDF5 datasets.
import h5pywrappers.dataset



##################################
## Define classes and functions ##
##################################

# List of public objects in objects.
__all__ = ["load",
           "save"]



def _check_and_convert_json_document_id(params):
    obj_name = "json_document_id"

    param_name_1 = "obj_id"
    param_name_2 = "name_of_obj_alias_of_"+param_name_1
    params = params.copy()
    params[param_name_2] = obj_name
    params[param_name_1] = params[params[param_name_2]]

    module_alias = h5pywrappers.obj
    func_alias = module_alias._check_and_convert_obj_id
    json_document_id = func_alias(params)

    return json_document_id



def load(json_document_id):
    r"""Load a JSON document from an HDF5 file.

    A JSON document is a dictionary that can be directly serialized into the
    JSON format. JSON documents are stored as ``bytes`` objects or ``numpy``
    bytes arrays in HDF5 files.

    Parameters
    ----------
    json_document_id : :class:`h5pywrappers.obj.ID`
        The parameter set specifying the JSON document of interest.

    Returns
    -------
    json_document : `dict`
        The JSON document of interest.

    """
    params = locals()
    global_symbol_table = globals()
    for param_name in params:
        func_name = "_check_and_convert_" + param_name
        func_alias = global_symbol_table[func_name]
        params[param_name] = func_alias(params)

    kwargs = params
    json_document = _load(**kwargs)

    return json_document



def _load(json_document_id):
    current_func_name = "_load"

    try:
        kwargs = {"dataset_id": json_document_id, "read_only": True}
        dataset = h5pywrappers.dataset.load(**kwargs)
        json_document = json.loads(dataset[()])
        if not isinstance(json_document, dict):
            raise
        dataset.file.close()
    except:
        dataset.file.close()
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise TypeError(err_msg)

    return json_document



def _check_and_convert_json_document(params):
    obj_name = "json_document"
    obj = params[obj_name]

    accepted_types = (dict, h5py._hl.dataset.Dataset)

    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_types": accepted_types}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)
    json_document = obj

    return json_document



def _check_and_convert_write_mode(params):
    module_alias = h5pywrappers.dataset
    func_alias = module_alias._check_and_convert_write_mode
    write_mode = func_alias(params)

    return write_mode



_module_alias = h5pywrappers.dataset
_default_write_mode = _module_alias._default_write_mode



def save(json_document, json_document_id, write_mode=_default_write_mode):
    r"""Save a JSON document to an HDF5 file.

    A JSON document is a dictionary that can be directly serialized into the
    JSON format. JSON documents are stored as ``bytes`` objects or ``numpy``
    bytes arrays in HDF5 files.

    Parameters
    ----------
    json_document : `dict` | :class:`h5py.Dataset`
        The JSON document of interest to save to an HDF5 file.
    json_document_id : :class:`h5pywrappers.obj.ID`
        The parameter set specifying where to save the JSON document of 
        interest.
    write_mode : "w" | "w-" | "a" | "a-", optional
        The write mode upon opening the HDF5 file to which to save the HDF5 JSON
        document of interest: if ``write_mode`` is set to ``"w"``, then the
        target HDF5 file is emptied prior to saving the HDF5 JSON document of
        interest; else if ``write_mode`` is set to ``"w-"``, then the HDF5 JSON
        document of interest is saved unless a file already exists with the
        target filename, in which case an error is raised and the target HDF5
        file is left unmodified; else if ``write_mode`` is set to ``"a-"``, then
        the HDF5 JSON document of interest is saved unless an HDF5 object
        already exists at the target HDF5 path of the target HDF5 file, in which
        case an error is raised and the target HDF5 file is left unmodified;
        else if ``write_mode`` is set to ``"a"``, then the HDF5 JSON document of
        interest is saved without emptying the target HDF5 file, replacing any
        HDF5 object at the target HDF5 path should one exist prior to saving.

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



def _save(json_document, json_document_id, write_mode):
    current_func_name = "_save"

    try:
        if isinstance(json_document, dict):
            serialized_json_document = json.dumps(json_document)
        else:
            serialized_json_document = json_document[()]
            if not isinstance(json.loads(serialized_json_document), dict):
                json_document.file.close()
                raise
    except:
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise TypeError(err_msg)

    kwargs = {"dataset": serialized_json_document,
              "dataset_id": json_document_id,
              "write_mode": write_mode}
    h5pywrappers.dataset.save(**kwargs)

    return None



###########################
## Define error messages ##
###########################

_load_err_msg_1 = \
    ("The object at the HDF5 path of the HDF5 file specified by the parameter "
     "``json_document_id`` is not of the expected type, i.e. a JSON-serialized "
     "dictionary stored as a ``bytes`` object or a ``numpy`` bytes array.")

_save_err_msg_1 = \
    ("The object ``json_document`` must be either a JSON-serializable "
     "dictionary or a zero-dimensional HDF5 dataset that stores a "
     "JSON-serialized dictionary as a ``bytes`` object or a ``numpy`` bytes "
     "array.")
