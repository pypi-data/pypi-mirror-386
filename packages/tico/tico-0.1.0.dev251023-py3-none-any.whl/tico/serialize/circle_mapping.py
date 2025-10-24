# Copyright (c) 2025 Samsung Electronics Co., Ltd. All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Optional, Sequence, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    import torch.fx
import numpy as np
import torch
from circle_schema import circle


# Convert torch dtype to circle dtype
def to_circle_dtype(
    torch_dtype: torch.dtype,
) -> int:
    assert isinstance(torch_dtype, torch.dtype)
    dmap = {
        torch.float32: circle.TensorType.TensorType.FLOAT32,
        torch.float: circle.TensorType.TensorType.FLOAT32,
        torch.uint8: circle.TensorType.TensorType.UINT8,
        torch.int8: circle.TensorType.TensorType.INT8,
        torch.int16: circle.TensorType.TensorType.INT16,
        torch.short: circle.TensorType.TensorType.INT16,
        torch.int32: circle.TensorType.TensorType.INT32,
        torch.int: circle.TensorType.TensorType.INT32,
        torch.int64: circle.TensorType.TensorType.INT64,
        torch.bool: circle.TensorType.TensorType.BOOL,
    }

    if torch_dtype not in dmap:
        raise RuntimeError(f"Unsupported dtype {torch_dtype}")

    circle_type = dmap[torch_dtype]
    assert circle_type is not None
    return circle_type


# Convert str dtype used in QuantParam to circle dtype
def str_to_circle_dtype(
    str_dtype: str,
) -> int:
    dmap = {
        "float32": circle.TensorType.TensorType.FLOAT32,
        "float": circle.TensorType.TensorType.FLOAT32,
        "uint8": circle.TensorType.TensorType.UINT8,
        "int8": circle.TensorType.TensorType.INT8,
        "int16": circle.TensorType.TensorType.INT16,
        "short": circle.TensorType.TensorType.INT16,
        "int32": circle.TensorType.TensorType.INT32,
        "int": circle.TensorType.TensorType.INT32,
        "int64": circle.TensorType.TensorType.INT64,
        "bool": circle.TensorType.TensorType.BOOL,
        "uint4": circle.TensorType.TensorType.UINT4,
        # TODO Add more dtypes
    }

    if str_dtype not in dmap:
        raise RuntimeError(f"Unsupported dtype {str_dtype}")

    circle_type = dmap[str_dtype]
    assert circle_type is not None
    return circle_type


# Convert circle dtype to numpy dtype
def np_dtype_from_circle_dtype(circle_dtype: int):
    dmap = {
        circle.TensorType.TensorType.FLOAT32: np.float32,
        circle.TensorType.TensorType.UINT8: np.uint8,
        circle.TensorType.TensorType.INT8: np.int8,
        circle.TensorType.TensorType.INT16: np.int16,
        circle.TensorType.TensorType.INT32: np.int32,
        circle.TensorType.TensorType.INT64: np.int64,
        circle.TensorType.TensorType.BOOL: np.bool_,
    }

    if circle_dtype not in dmap:
        raise RuntimeError(f"Unsupported dtype {circle_dtype}")

    np_dtype = dmap[circle_dtype]
    assert np_dtype is not None
    return np_dtype


# Return dtype of node
def extract_torch_dtype(node: torch.fx.Node) -> torch.dtype:
    assert node.meta is not None
    assert node.meta.get("val") is not None

    val = node.meta.get("val")
    val_dtype = None
    if isinstance(val, torch.Tensor):
        assert isinstance(val.dtype, torch.dtype)
        val_dtype = val.dtype
    else:
        val_dtype = torch.tensor(val).dtype
    return val_dtype


def extract_circle_dtype(node: torch.fx.Node) -> int:
    return to_circle_dtype(extract_torch_dtype(node))


# Return shape of node
def extract_shape(node: torch.fx.Node) -> torch.Size:
    assert node.meta is not None
    assert node.meta.get("val") is not None

    val = node.meta.get("val")
    val_shape = None
    if isinstance(val, torch.Tensor):
        val_shape = val.size()
    else:
        val_shape = torch.tensor(val).shape

    return val_shape


def extract_circle_shape(node: torch.fx.Node) -> Tuple[List[int], Optional[List[int]]]:
    return to_circle_shape(extract_shape(node))


def to_circle_shape(
    torch_shape: Union[
        torch.Size, Sequence[int | torch.SymInt]
    ],  # Sequence[int | torch.SymInt] is added for type covariance
) -> Tuple[List[int], Optional[List[int]]]:

    if any(isinstance(s, torch.SymInt) for s in torch_shape):
        # Follow dynamic shape spec
        shape = []
        shape_signature = []
        for s in torch_shape:
            if isinstance(s, torch.SymInt):
                shape.append(1)
                shape_signature.append(-1)
            elif isinstance(s, int):
                shape.append(s)
                shape_signature.append(s)
            else:
                raise RuntimeError(f"Unsupported shape {torch_shape}")
        return shape, shape_signature
    else:
        # Follow static shape spec
        shape = []
        shape_signature = None
        for s in torch_shape:
            if isinstance(s, int):
                shape.append(s)
            else:
                assert False, "Cannot reach here"
        return shape, shape_signature


def validate_circle_shape(shape: List[int], shape_signature: Optional[List[int]]):
    """
    Validate circle tensor shape and shape_signature.
    @ref https://github.com/Samsung/TICO/issues/244
    """
    if shape_signature is not None:
        if len(shape_signature) == 0:
            raise ValueError(
                "Invalid circle shape: shape_signature must not be an empty list. "
                "For static shapes, use None instead of []."
            )
        if len(shape) != len(shape_signature):
            raise ValueError(
                f"Invalid circle shape: shape and shape_signature must have same length: {shape} {shape_signature}"
            )
        if not all(isinstance(s, int) for s in shape_signature):
            raise ValueError(
                f"circle tensor shape_signature must be all integer values. {shape_signature}"
            )
        for s, ss in zip(shape, shape_signature):
            if ss == -1:
                # dynamic shape dimension
                if s != 1:
                    raise ValueError(
                        f"Invalid circle shape: {s} {ss} {shape} {shape_signature}"
                    )
            else:
                # static shape dimension
                if s != ss:
                    raise ValueError(
                        f"Invalid circle shape: {s} {ss} {shape} {shape_signature}"
                    )

    if not all(isinstance(s, int) for s in shape):
        raise ValueError(f"circle tensor shape must be all integer values. {shape}")


# Return stride of node
def extract_stride(node: torch.fx.Node) -> Tuple[int, ...]:
    assert node.meta is not None
    assert node.meta.get("val") is not None

    val = node.meta.get("val")
    val_stride = None
    assert isinstance(val, torch.Tensor)
    val_stride = val.stride()

    return val_stride


def traverse_elements(iter, container_types=(list, tuple)):
    if isinstance(iter, container_types):
        for e in iter:
            for sub_e in traverse_elements(e, container_types):
                yield sub_e
    else:
        yield iter


def check_if_i32_range(axis: Union[list, int]):
    INT32_MAX = 2**31 - 1
    INT32_MIN = -(2**31)
    values = list(traverse_elements(axis))
    return all(INT32_MIN <= val <= INT32_MAX for val in values)


# TODO: Revisit this dtype legalization function as it breaks SRP
def circle_legalize_dtype_to(values, *, dtype: torch.dtype) -> torch.Tensor:
    """
    Legalize data types from `torch.int64` to `torch.int32`.

    Pytorch assumes python's built-in integer type is `torch.int64`.
    But, many of the circle infrastructures support only int32 type. E.g. circle-interpreter.

    So, if constants has values whose range is inside [INT32_MIN <= val <= INT32_MAX], we will legalize the data type to int32.

    TODO support more types

    NOTE. This function must be applied only to constant values.
    """
    if dtype != torch.int32:
        raise RuntimeError("Not supported data types.")
    if not check_if_i32_range(values):
        raise RuntimeError("'size' cannot be converted from int64 to int32.")
    return torch.as_tensor(values, dtype=dtype)
