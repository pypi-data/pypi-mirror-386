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
r"""For loading and saving HDF5 "datasubsets".

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For general array handling.
import numpy as np

# For updating HDF5 datasets.
import h5py

# For validating and converting objects.
import czekitout.check
import czekitout.convert

# For defining classes that support enforced validation, updatability,
# pre-serialization, and de-serialization.
import fancytypes



# For loading and saving HDF5 datasets.
import h5pywrappers.dataset



##################################
## Define classes and functions ##
##################################

# List of public objects in objects.
__all__ = ["ID",
           "load",
           "save"]



def _check_and_convert_dataset_id(params):
    module_alias = h5pywrappers.dataset
    func_alias = module_alias._check_and_convert_dataset_id
    dataset_id = func_alias(params)

    return dataset_id



def _pre_serialize_dataset_id(dataset_id):
    obj_to_pre_serialize = dataset_id

    obj_name = "dataset_id"
    
    module_alias = h5pywrappers.dataset
    func_alias = module_alias._pre_serialize_dataset_id
    kwargs = {obj_name: obj_to_pre_serialize}
    serializable_rep = func_alias(**kwargs)
    
    return serializable_rep



def _de_pre_serialize_dataset_id(serializable_rep):
    module_alias = h5pywrappers.dataset
    func_alias = module_alias._de_pre_serialize_dataset_id
    dataset_id = func_alias(serializable_rep)

    return dataset_id



def _check_and_convert_multi_dim_slice(params):
    obj_name = "multi_dim_slice"
    obj = params[obj_name]

    current_func_name = "_check_and_convert_multi_dim_slice"

    if obj is not None:
        try:
            kwargs = {"obj": obj, "obj_name": obj_name}
            multi_dim_slice = czekitout.convert.to_multi_dim_slice(**kwargs)
        except:
            unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
            err_msg = unformatted_err_msg.format(obj_name)
            raise TypeError(err_msg)
    else:
        multi_dim_slice = None

    return multi_dim_slice



def _pre_serialize_multi_dim_slice(multi_dim_slice):
    if multi_dim_slice is not None:
        serializable_rep = list(multi_dim_slice)
        for idx, single_dim_slice in enumerate(multi_dim_slice):
            if isinstance(single_dim_slice, slice):
                serializable_rep[idx] = {"start": single_dim_slice.start,
                                         "stop": single_dim_slice.stop,
                                         "step": single_dim_slice.step}
        serializable_rep = tuple(serializable_rep)
    else:
        serializable_rep = multi_dim_slice
    
    return serializable_rep



def _de_pre_serialize_multi_dim_slice(serializable_rep):
    if serializable_rep is not None:
        multi_dim_slice = list(serializable_rep)
        for idx, elem_of_serializable_rep in enumerate(serializable_rep):
            if isinstance(elem_of_serializable_rep, dict):
                multi_dim_slice[idx] = slice(elem_of_serializable_rep["start"],
                                             elem_of_serializable_rep["stop"],
                                             elem_of_serializable_rep["step"])
        multi_dim_slice = tuple(multi_dim_slice)
    else:
        multi_dim_slice = serializable_rep

    return multi_dim_slice



_module_alias = \
    h5pywrappers.obj
_default_multi_dim_slice = \
    None
_default_skip_validation_and_conversion = \
    _module_alias._default_skip_validation_and_conversion



class ID(fancytypes.PreSerializableAndUpdatable):
    r"""A parameter set specifying an HDF5 "datasubset" in an HDF5 file.

    By "datasubset", we mean an array obtained by taking a multidimensional 
    slice of an HDF5 dataset in an HDF5 file.

    Parameters
    ----------
    dataset_id : :class:`h5pywrappers.obj.ID`
        The parameter set specifying the target HDF5 dataset containing the HDF5
        datasubset of interest.
    multi_dim_slice : `tuple` (`int` | `slice` | `list` (`int`)) | `None`, optional
        The "multidimensional slice object", which specifies the
        multidimensional slice of the target HDF5 dataset that yields the HDF5
        datasubset of interest. We define a multi-dimensional slice object as a
        `tuple` of items which contains at most one item being a `list` of
        integers, and the remaining items being `slice` and/or `int`
        objects. Let ``dataset`` and ``datasubset`` be the target HDF5 dataset
        and datasubset respectively. If ``multi_dim_slice`` is set to `None`,
        then ``datasubset == dataset[()]``. Otherwise, if ``multi_dim_slice`` is
        array-like, then ``multi_dim_slice`` satisfies ``datasubset ==
        dataset[()][multi_dim_slice]``, however the actual implementation of the
        multidimensional slice is more efficient than the above.
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
    ctor_param_names = ("dataset_id", "multi_dim_slice")
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
                 dataset_id,
                 multi_dim_slice=\
                 _default_multi_dim_slice,
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



def _check_and_convert_datasubset_id(params):
    obj_name = "datasubset_id"
    obj = params[obj_name]
    
    accepted_types = (ID,)

    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_types": accepted_types}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)
    datasubset_id = obj

    return datasubset_id



def load(datasubset_id):
    r"""Load an HDF5 "datasubset" from an HDF5 file.

    By "datasubset", we mean an array obtained by taking a multidimensional
    slice of an HDF5 dataset in an HDF5 file.

    Parameters
    ----------
    datasubset_id : :class:`h5pywrappers.datasubset.ID`
        The parameter set specifying the HDF5 datasubset of interest.

    Returns
    -------
    datasubset : `array_like`
        The HDF5 datasubset of interest.

    """
    params = locals()
    global_symbol_table = globals()
    for param_name in params:
        func_name = "_check_and_convert_" + param_name
        func_alias = global_symbol_table[func_name]
        params[param_name] = func_alias(params)

    kwargs = params
    datasubset = _load(**kwargs)

    return datasubset



def _load(datasubset_id):
    kwargs = {"datasubset_id": datasubset_id, "datasubset": None}
    multi_dim_slice_triplet = _calc_multi_dim_slice_triplet(**kwargs)

    multi_dim_slice_1 = multi_dim_slice_triplet[0]
    multi_dim_slice_2 = multi_dim_slice_triplet[1]
    multi_dim_slice_3 = multi_dim_slice_triplet[2]

    datasubset_id_core_attrs = datasubset_id.get_core_attrs(deep_copy=False)
    dataset_id = datasubset_id_core_attrs["dataset_id"]

    current_func_name = "_load"

    kwargs = {"multi_dim_slice": multi_dim_slice_1,
              "task_requiring_transpose": current_func_name[1:]}
    axes_ordering_for_transpose = _calc_axes_ordering_for_transpose(**kwargs)
    
    dataset = h5pywrappers.dataset.load(dataset_id, read_only=True)

    kwargs = {"a": dataset[multi_dim_slice_2][multi_dim_slice_3],
              "axes": axes_ordering_for_transpose}
    datasubset = np.transpose(**kwargs)
    
    dataset.file.close()

    return datasubset



def _calc_multi_dim_slice_triplet(datasubset_id, datasubset):
    datasubset_id_core_attrs = datasubset_id.get_core_attrs(deep_copy=False)
    dataset_id = datasubset_id_core_attrs["dataset_id"]
    
    dataset = h5pywrappers.dataset.load(dataset_id, read_only=True)
    dataset_shape = dataset.shape
    dataset.file.close()

    multi_dim_slice_1 = _calc_multi_dim_slice_1(datasubset_id, dataset_shape)

    task_requiring_transpose = ("load"
                                if (datasubset is None)
                                else "save")

    kwargs = {"multi_dim_slice": multi_dim_slice_1,
              "task_requiring_transpose": task_requiring_transpose}
    axes_ordering_for_transpose = _calc_axes_ordering_for_transpose(**kwargs)

    kwargs = {"datasubset_id": datasubset_id,
              "datasubset": datasubset,
              "dataset_shape": dataset_shape,
              "multi_dim_slice_1": multi_dim_slice_1,
              "axes_ordering_for_transpose": axes_ordering_for_transpose}
    multi_dim_slices_2_and_3 = _calc_multi_dim_slices_2_and_3(**kwargs)
    
    multi_dim_slice_2 = multi_dim_slices_2_and_3[0]
    multi_dim_slice_3 = multi_dim_slices_2_and_3[1]

    multi_dim_slice_triplet = (multi_dim_slice_1,
                               multi_dim_slice_2,
                               multi_dim_slice_3)

    return multi_dim_slice_triplet



def _calc_multi_dim_slice_1(datasubset_id, dataset_shape):
    datasubset_id_core_attrs = datasubset_id.get_core_attrs(deep_copy=False)
    
    dataset_rank = len(dataset_shape)

    current_func_name = "_calc_multi_dim_slice_1"

    multi_dim_slice_1 = datasubset_id_core_attrs["multi_dim_slice"]
    if multi_dim_slice_1 is None:
        multi_dim_slice_1 = tuple(slice(None) for _ in range(dataset_rank))

    if len(multi_dim_slice_1) != dataset_rank:
        dataset_id = datasubset_id_core_attrs["dataset_id"]
        
        dataset_id_core_attrs = dataset_id.get_core_attrs(deep_copy=False)
        path_in_file = dataset_id_core_attrs["path_in_file"]
        filename = dataset_id_core_attrs["filename"]
        
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(path_in_file, filename)
        raise IndexError(err_msg)

    multi_dim_slice_1 = tuple(multi_dim_slice_1)

    return multi_dim_slice_1



def _calc_multi_dim_slices_2_and_3(datasubset_id,
                                   datasubset,
                                   dataset_shape,
                                   multi_dim_slice_1,
                                   axes_ordering_for_transpose):
    datasubset_id_core_attrs = datasubset_id.get_core_attrs(deep_copy=False)
    dataset_id = datasubset_id_core_attrs["dataset_id"]
    
    dataset_rank = len(dataset_shape)

    multi_dim_slice_2 = tuple()
    multi_dim_slice_3 = tuple()

    if datasubset is not None:
        datasubset_shape = []

    for axis in range(dataset_rank):
        single_dim_slice_1 = multi_dim_slice_1[axis]
        max_allowed_idx = dataset_shape[axis]-1

        kwargs = {"single_dim_slice_1": single_dim_slice_1,
                  "max_allowed_idx": max_allowed_idx,
                  "axis": axis,
                  "dataset_id": dataset_id}
        single_dim_slice_triplet = _calc_single_dim_slice_triplet(**kwargs)
        
        single_dim_slice_2 = single_dim_slice_triplet[1]
        single_dim_slice_3 = single_dim_slice_triplet[2]
                            
        multi_dim_slice_2 += (single_dim_slice_2,)
        if single_dim_slice_3 is not None:
            multi_dim_slice_3 += (single_dim_slice_3,)
            if datasubset is not None:
                dataset_dim = dataset_shape[axis]
                datasubset_dim = len(np.arange(dataset_dim)[single_dim_slice_2])
                datasubset_shape.append(datasubset_dim)

    current_func_name = "_calc_multi_dim_slices_2_and_3"
                
    if datasubset is not None:
        datasubset_shape = tuple(datasubset_shape[axis_idx]
                                 for axis_idx
                                 in axes_ordering_for_transpose)
        if datasubset_shape != datasubset.shape:
            err_msg = globals()[current_func_name+"_err_msg_1"]
            raise ValueError(err_msg)

    multi_dim_slices_2_and_3 = (multi_dim_slice_2, multi_dim_slice_3)

    return multi_dim_slices_2_and_3



def _calc_single_dim_slice_triplet(single_dim_slice_1,
                                   max_allowed_idx,
                                   axis,
                                   dataset_id):
    kwargs = locals()

    if isinstance(single_dim_slice_1, list):
        func_alias = _calc_single_dim_slice_triplet_for_case_1
    elif isinstance(single_dim_slice_1, int):
        func_alias = _calc_single_dim_slice_triplet_for_case_2
    else:  # If a `slice` object.
        func_alias = _calc_single_dim_slice_triplet_for_case_3
        del kwargs["axis"]
        del kwargs["dataset_id"]

    single_dim_slice_triplet = func_alias(**kwargs)

    return single_dim_slice_triplet



def _calc_single_dim_slice_triplet_for_case_1(single_dim_slice_1,
                                              max_allowed_idx,
                                              axis,
                                              dataset_id):
    temp = []
    for idx in single_dim_slice_1:
        idx = _check_and_shift_idx(idx, max_allowed_idx, axis, dataset_id)
        temp.append(idx)

    current_func_name = "_calc_single_dim_slice_triplet_for_case_1"
            
    if len(temp) != len(set(temp)):
        dataset_id_core_attrs = dataset_id.get_core_attrs(deep_copy=False)
        path_in_file = dataset_id_core_attrs["path_in_file"]
        filename = dataset_id_core_attrs["filename"]
        
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(axis, path_in_file, filename)
        raise ValueError(err_msg)
        
    single_dim_slice_2 = list(np.sort(temp))
    sort_order = np.argsort(temp)
    single_dim_slice_3 = [0]*len(temp)
    for idx in range(len(temp)):
        single_dim_slice_3[sort_order[idx]] = idx

    single_dim_slice_triplet = (single_dim_slice_1,
                                single_dim_slice_2,
                                single_dim_slice_3)

    return single_dim_slice_triplet



def _calc_single_dim_slice_triplet_for_case_2(single_dim_slice_1,
                                              max_allowed_idx,
                                              axis,
                                              dataset_id):
    kwargs = {"idx": single_dim_slice_1,
              "max_allowed_idx": max_allowed_idx,
              "axis": axis,
              "dataset_id": dataset_id}
    single_dim_slice_2 = _check_and_shift_idx(**kwargs)
    
    single_dim_slice_3 = None

    single_dim_slice_triplet = (single_dim_slice_1,
                                single_dim_slice_2,
                                single_dim_slice_3)

    return single_dim_slice_triplet



def _check_and_shift_idx(idx, max_allowed_idx, axis, dataset_id):
    idx = (max_allowed_idx+1)+idx if (idx < 0) else idx
    current_func_name = "_check_and_shift_idx"

    if (idx < 0) or (idx > max_allowed_idx):
        dataset_id_core_attrs = dataset_id.get_core_attrs(deep_copy=False)
        path_in_file = dataset_id_core_attrs["path_in_file"]
        filename = dataset_id_core_attrs["filename"]

        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(axis, path_in_file, filename)
        raise ValueError(err_msg)

    return idx



def _calc_single_dim_slice_triplet_for_case_3(single_dim_slice_1,
                                              max_allowed_idx):
    single_dim_slice_2_step = int(np.abs(single_dim_slice_1.step or 1))
    single_dim_slice_3_step = int(np.sign(single_dim_slice_1.step or 1))
    
    if single_dim_slice_3_step > 0:
        single_dim_slice_2 = slice(single_dim_slice_1.start,
                                   single_dim_slice_1.stop,
                                   single_dim_slice_2_step)
    else:
        temp_1 = (min(single_dim_slice_1.start, max_allowed_idx)
                  if (single_dim_slice_1.start is not None)
                  else max_allowed_idx)
        if temp_1 < 0:
            temp_1 = max((max_allowed_idx+1)+temp_1, 0)

        temp_2 = (min(single_dim_slice_1.stop, max_allowed_idx)
                  if (single_dim_slice_1.stop is not None)
                  else -1)
        if (temp_2 < 0) and (single_dim_slice_1.stop is not None):
            temp_2 = max((max_allowed_idx+1)+temp_2, -1)

        temp_3 = single_dim_slice_2_step
        temp_4 = (temp_1 - temp_2 - 1) // temp_3

        single_dim_slice_2_start = temp_1 - temp_3*temp_4
        single_dim_slice_2_stop = temp_1 + 1
            
        single_dim_slice_2 = slice(single_dim_slice_2_start,
                                   single_dim_slice_2_stop,
                                   single_dim_slice_2_step)
        
    single_dim_slice_3 = slice(None, None, single_dim_slice_3_step)

    single_dim_slice_triplet = (single_dim_slice_1,
                                single_dim_slice_2,
                                single_dim_slice_3)

    return single_dim_slice_triplet



def _calc_axes_ordering_for_transpose(multi_dim_slice,
                                      task_requiring_transpose):
    pop_idx = 0
    insert_idx = 0
    non_scalar_single_dim_slice_count = 0
    num_advanced_array_idx_clusters = 0
    last_single_dim_slice_was_a_slice = None
    axes_ordering_for_transpose = []

    for axis_idx, single_dim_slice in enumerate(multi_dim_slice):
        if isinstance(single_dim_slice, (int, list)):
            if last_single_dim_slice_was_a_slice is None:
                num_advanced_array_idx_clusters += 1
            elif last_single_dim_slice_was_a_slice:
                num_advanced_array_idx_clusters += 1

            last_single_dim_slice_was_a_slice = False
            
            if isinstance(single_dim_slice, list):
                if task_requiring_transpose == "load":
                    pop_idx = non_scalar_single_dim_slice_count
                    insert_idx = 0
                else:
                    pop_idx = 0
                    insert_idx = non_scalar_single_dim_slice_count
        else:
            last_single_dim_slice_was_a_slice = True

        if isinstance(single_dim_slice, (slice, list)):
            axes_ordering_for_transpose += [non_scalar_single_dim_slice_count]
            non_scalar_single_dim_slice_count += 1

    if num_advanced_array_idx_clusters > 1:
        popped_item = axes_ordering_for_transpose.pop(pop_idx)
        axes_ordering_for_transpose.insert(insert_idx, popped_item)
            
    axes_ordering_for_transpose = tuple(axes_ordering_for_transpose)

    return axes_ordering_for_transpose



def _check_and_convert_datasubset(params):
    obj_name = "datasubset"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    datasubset = czekitout.convert.to_numpy_array(**kwargs)

    return datasubset



def save(datasubset, datasubset_id):
    r"""Save an HDF5 attribute to an HDF5 file.

    By "datasubset", we mean an array obtained by taking a multidimensional
    slice of an HDF5 dataset in an HDF5 file.

    Note that if the HDF5 datasubset to be saved is of a different data type
    than the aforementioned HDF5 dataset, then the current Python function will
    try to convert a copy of the former to the same data type as the latter.

    Parameters
    ----------
    datasubset : `array_like`
        The HDF5 datasubset of interest to save to an HDF5 file.
    datasubset_id : :class:`h5pywrappers.datasubset.ID`
        The parameter set specifying where to save the HDF5 datasubset of
        interest.

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



def _save(datasubset, datasubset_id):
    kwargs = {"datasubset_id": datasubset_id, "datasubset": datasubset}
    multi_dim_slice_triplet = _calc_multi_dim_slice_triplet(**kwargs)

    multi_dim_slice_1 = multi_dim_slice_triplet[0]
    multi_dim_slice_2 = multi_dim_slice_triplet[1]
    multi_dim_slice_3 = multi_dim_slice_triplet[2]

    datasubset_id_core_attrs = datasubset_id.get_core_attrs(deep_copy=False)
    dataset_id = datasubset_id_core_attrs["dataset_id"]

    current_func_name = "_save"

    kwargs = {"multi_dim_slice": multi_dim_slice_1,
              "task_requiring_transpose": current_func_name[1:]}
    axes_ordering_for_transpose = _calc_axes_ordering_for_transpose(**kwargs)
    
    dataset = h5pywrappers.dataset.load(dataset_id, read_only=False)
    
    try:
        kwargs = {"a": datasubset, "axes": axes_ordering_for_transpose}
        dataset[multi_dim_slice_2] = np.transpose(**kwargs)[multi_dim_slice_3]
    except:
        dataset.file.close()

        dataset_id_core_attrs = dataset_id.get_core_attrs(deep_copy=False)
        path_in_file = dataset_id_core_attrs["path_in_file"]
        filename = dataset_id_core_attrs["filename"]

        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(path_in_file, filename)
        raise IOError(err_msg)

    dataset.file.close()

    return None



###########################
## Define error messages ##
###########################

_check_and_convert_multi_dim_slice_err_msg_1 = \
    ("The object ``{}`` must be either an instance of `NoneType` or a sequence "
     "of items which contains at most one item being a sequence of integers, "
     "and the remaining items being `slice` objects and/or integers.")

_calc_multi_dim_slice_1_err_msg_1 = \
    ("The 'multidimensional slice object', specified by the object "
     "``datasubset_id``, must be a sequence of length equal to the rank of the "
     "HDF5 dataset at the HDF5 path ``'{}'`` of the HDF5 file at the file path "
     "``'{}'``.")

_calc_multi_dim_slices_2_and_3_err_msg_1 = \
    ("The 'multidimensional slice object', specified by the object "
     "``datasubset_id``, implies an HDF5 datasubset with dimensions that are "
     "incompatible with those of the HDF5 datasubset ``datasubset``.")

_calc_single_dim_slice_triplet_for_case_1_err_msg_1 = \
    ("The slice for the dataset axis #{}, specified by the object "
     "``datasubset_id``, is of incorrect format: the slice contains repeating "
     "indices after converting any negative indices to their functionally "
     "equivalent positive values.")

_check_and_shift_idx_err_msg_1 = \
    ("The slice for the dataset axis #{}, specified by the object "
     "``datasubset_id``, is of incorrect format: the slice contains at least "
     "one index that is out of the bounds of the HDF5 dataset at the HDF5 path "
     "``'{}'`` of the HDF5 file at the file path ``'{}'``.")

_save_err_msg_1 = \
    ("An error occurred in trying to save the HDF5 datasubset ``datasubset`` "
     "to the HDF5 dataset at the HDF5 path ``'{}'`` of the HDF5 file at the "
     "file path ``'{}'``. Perhaps the HDF5 datasubet and dataset are of "
     "imcompatible data types. See the remaining traceback for details.")
