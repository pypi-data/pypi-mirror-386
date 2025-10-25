# jax2onnx/plugins/jax/lax/gather_helpers.py

from typing import Any, Callable
import numpy as np


def check_uniform_start_index(
    indices_var_value: np.ndarray, indices_var_idx: int
) -> bool:
    values = np.reshape(indices_var_value[..., indices_var_idx], (-1,))
    return all(values == values[0])


def transpose_to_gir(indices: list[int], input_shape: list[Any]) -> list[dict]:
    if indices == list(range(len(indices))):
        return []
    dims = [
        {
            "dim": src_idx,
            "mode": "transpose",
            "target_dimensions": [target_idx],
            "target_dimensions_shape": [input_shape[src_idx]],
        }
        for src_idx, target_idx in enumerate(indices)
    ]
    return [
        {"op": "transpose", "dims": dims, "numpy_transpose": invert_transpose(indices)}
    ]


def index_transpose_to_gir(indices: list[int], input_shape: list[Any]) -> list[dict]:
    if indices == list(range(len(indices))):
        return []
    dims = [
        {
            "dim": src_idx,
            "mode": "transpose",
            "target_dimensions": [target_idx],
            "target_dimensions_shape": [input_shape[src_idx]],
        }
        for src_idx, target_idx in enumerate(indices)
    ]
    return [
        {
            "op": "index_transpose",
            "dims": dims,
            "numpy_transpose": invert_transpose(indices),
        }
    ]


def index_lastdim_gather_to_gir(
    gather_indices: list[int], input_shape: list[int]
) -> list[dict]:
    return [
        {
            "op": "index_lastdim_gather",
            "gather_indices": gather_indices,
            "input_shape": input_shape,
        }
    ]


def index_expand_range_gir(
    dims_to_extend: list[int], dim_slice_sizes: list[int], input_shape: list[int]
) -> list[dict]:
    dims = [
        {"mode": "expand", "indices_var_index": dim_idx, "slice_size": slice_size}
        for dim_idx, slice_size in zip(dims_to_extend, dim_slice_sizes)
    ]
    return [{"op": "index_expand", "new_dims": dims, "input_shape": input_shape}]


def index_reshape(input_shape: list[int], new_shape: list[int]):
    return [
        {"op": "index_reshape", "input_shape": input_shape, "output_shape": new_shape}
    ]


def invert_transpose(indices: list[int]) -> list[int]:
    assert set(indices) == set(range(len(indices)))
    result = [-1] * len(indices)
    for i, idx in enumerate(indices):
        result[idx] = i
    return result


def get_gir_input_shape(gir_instr: dict) -> list[Any]:
    if "dims" not in gir_instr:
        return gir_instr["input_shape"]
    else:
        return [dim["input_size"] for dim in gir_instr["dims"]]


def get_gir_output_shape(gir_instr: dict) -> list[Any]:
    index_to_shape_map = {}
    if "dims" not in gir_instr:
        return gir_instr["output_shape"]
    else:
        for dim in gir_instr["dims"]:
            for idx, size in zip(
                dim["target_dimensions"], dim["target_dimensions_shape"]
            ):
                index_to_shape_map[idx] = size
        return [index_to_shape_map[i] for i in range(len(index_to_shape_map))]


def calculate_index_shape(gir_instr: dict) -> list[Any]:
    assert gir_instr["op"] in ["general_gather", "ONNX_GatherND"]
    index_shape = {}
    index_index = []
    gather_shape = []
    num_gather_output_dim = 0
    num_gatherlike_dims = 0

    for dim in gir_instr["dims"]:
        if dim["mode"] == "batched":
            assert len(dim["target_dimensions_shape"]) == 1
            index_index.append(dim["indices_dim"])
            index_shape[dim["indices_dim"]] = dim["target_dimensions_shape"][0]
        elif dim["mode"] == "gather":
            num_gather_output_dim = len(dim["target_dimensions"])
            gather_shape = dim["target_dimensions_shape"]
            num_gatherlike_dims += 1
        elif "start_indices_var_index" in dim or "indices_var_index" in dim:
            num_gatherlike_dims += 1

    i = 0
    for j in range(num_gather_output_dim):
        while i in index_index:
            i += 1
        index_index.append(i)
        index_shape[i] = gather_shape[j]

    index_shape = [index_shape[i] for i in range(len(index_shape))]
    index_shape += [num_gatherlike_dims]

    return index_shape, index_index


def is_gather_nop(gir_instr: dict) -> bool:
    assert gir_instr["op"] == "general_gather"
    return all(
        dim["mode"] == "passthrough" and [dim["dim"]] == dim["target_dimensions"]
        for dim in gir_instr["dims"]
    )


def run_one_pass(
    gir: list[dict], one_pass: Callable[[dict], list[dict]], targets: list[str]
):
    result_gir = []
    for instr in gir:
        if instr["op"] in targets:
            result_gir += one_pass(instr)
        else:
            result_gir.append(instr)
    return result_gir
