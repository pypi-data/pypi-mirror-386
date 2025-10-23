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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch.fx
import copy

from collections import defaultdict
from typing import Any

import torch
from torch.export import ExportedProgram

from tico.serialize.quant_param import QPARAM_KEY, QuantParam
from tico.utils import logging
from tico.utils.errors import NotYetSupportedError
from tico.utils.graph import create_node
from tico.utils.passes import PassBase, PassResult
from tico.utils.trace_decorators import trace_graph_diff_on_pass
from tico.utils.utils import quant_min_max, set_new_meta_val
from tico.utils.validate_args_kwargs import (
    AddTensorArgs,
    BmmArgs,
    CatArgs,
    LinearArgs,
    MulTensorArgs,
    PermuteArgs,
    ReluArgs,
    ReshapeArgs,
)


def qparam_dtype(node: torch.fx.Node) -> str:
    assert QPARAM_KEY in node.meta
    return node.meta[QPARAM_KEY].dtype


# Convert i16 qparam to u8 qparam
# scale and zero_point are inferred from i16 qparam
def _i16_to_u8(qparam: QuantParam) -> QuantParam:
    # Assume per-tensor quantization
    assert qparam.scale is not None and len(qparam.scale) == 1
    assert qparam.dtype == "int16"

    s16_scale = qparam.scale[0]
    max_ = s16_scale * 32767  # numeric_limits<int16>
    min_ = -max_

    u8_scale = (max_ - min_) / 255
    u8_zerop = round(-min_ / u8_scale)

    new_qparam = QuantParam()
    new_qparam.scale = [u8_scale]
    new_qparam.zero_point = [u8_zerop]
    new_qparam.dtype = "uint8"

    return new_qparam


# Convert u8 qparam to i16 qparam
# scale is inferred from u8 qparam
def _u8_to_i16(qparam: QuantParam) -> QuantParam:
    # Assume per-tensor quantization
    assert qparam.scale is not None and len(qparam.scale) == 1
    assert qparam.zero_point is not None and len(qparam.zero_point) == 1
    assert qparam.dtype == "uint8"

    u8_scale = qparam.scale[0]
    u8_zerop = qparam.zero_point[0]
    max_ = u8_scale * (255 - u8_zerop)
    min_ = u8_scale * (-u8_zerop)

    abs_max = max(abs(max_), abs(min_))
    s16_scale = abs_max / 32767
    s16_zerop = 0

    new_qparam = QuantParam()
    new_qparam.scale = [s16_scale]
    new_qparam.zero_point = [s16_zerop]
    new_qparam.dtype = "int16"

    return new_qparam


def _insert_quantize_op_before(node, inp):
    graph = node.graph
    qparam: QuantParam = node.meta[QPARAM_KEY]
    assert qparam.scale is not None
    assert qparam.zero_point is not None
    scale = qparam.scale[0]
    zerop = qparam.zero_point[0]
    min_, max_ = quant_min_max(qparam.dtype)
    dtype = getattr(torch, qparam.dtype)

    with graph.inserting_before(node):
        q_args = (inp, scale, zerop, min_, max_, dtype)
        quantize = create_node(
            graph,
            torch.ops.quantized_decomposed.quantize_per_tensor.default,
            args=q_args,
            origin=node,
        )
        quantize.meta[QPARAM_KEY] = copy.deepcopy(qparam)
        set_new_meta_val(quantize)

    node.replace_input_with(inp, quantize)

    return quantize


def _insert_quantize_op_after(node):
    graph = node.graph
    qparam: QuantParam = node.meta[QPARAM_KEY]
    assert qparam.scale is not None
    assert qparam.zero_point is not None
    scale = qparam.scale[0]
    zerop = qparam.zero_point[0]
    min_, max_ = quant_min_max(qparam.dtype)
    dtype = getattr(torch, qparam.dtype)
    with graph.inserting_after(node):
        q_args = (node, scale, zerop, min_, max_, dtype)
        quantize = create_node(
            graph,
            torch.ops.quantized_decomposed.quantize_per_tensor.default,
            args=q_args,
        )

    node.replace_all_uses_with(quantize, propagate_meta=True)
    quantize.replace_input_with(quantize, node)

    quantize.meta[QPARAM_KEY] = copy.deepcopy(qparam)

    return quantize


def _linear_handler(node, logger):
    lin_args = LinearArgs(*node.args, **node.kwargs)
    inp = lin_args.input

    if QPARAM_KEY not in inp.meta:
        return

    if QPARAM_KEY not in node.meta:
        return

    if qparam_dtype(inp) == qparam_dtype(node):
        return

    if qparam_dtype(inp) == "uint8" and qparam_dtype(node) == "int16":
        quantize = _insert_quantize_op_after(node)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])

        # Update node's qparam from i16 to u8
        # NOTE This would severely degrade accuracy. It is
        # important to mitigate this accuracy drop in backend.
        node.meta[QPARAM_KEY] = _i16_to_u8(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted after {node.name}.")
    else:
        raise NotYetSupportedError(
            f"Unsupported dtype: From {qparam_dtype(inp)} to {qparam_dtype(node)}"
        )


def _add_handler(node, logger):
    add_args = AddTensorArgs(*node.args, **node.kwargs)
    x = add_args.input
    y = add_args.other

    if not isinstance(x, torch.fx.Node):
        return
    if not isinstance(y, torch.fx.Node):
        return

    if QPARAM_KEY not in x.meta:
        return
    if QPARAM_KEY not in y.meta:
        return
    if QPARAM_KEY not in node.meta:
        return

    if qparam_dtype(x) == qparam_dtype(node):
        return

    if qparam_dtype(x) != qparam_dtype(y):
        return

    if qparam_dtype(x) == "int16" and qparam_dtype(node) == "uint8":
        quantize = _insert_quantize_op_after(node)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        node.meta[QPARAM_KEY] = _u8_to_i16(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted after {node.name}.")
    else:
        raise NotYetSupportedError("Unsupported dtype")


def _mul_handler(node, logger):
    mul_args = MulTensorArgs(*node.args, **node.kwargs)
    x = mul_args.input
    y = mul_args.other

    if not isinstance(x, torch.fx.Node):
        return
    if not isinstance(y, torch.fx.Node):
        return

    if QPARAM_KEY not in x.meta:
        return
    if QPARAM_KEY not in y.meta:
        return
    if QPARAM_KEY not in node.meta:
        return

    if qparam_dtype(x) == qparam_dtype(node):
        return

    if qparam_dtype(x) == "int16" and qparam_dtype(node) == "uint8":
        quantize = _insert_quantize_op_after(node)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        node.meta[QPARAM_KEY] = _u8_to_i16(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted after {node.name}.")
    else:
        raise NotYetSupportedError("Unsupported dtype")


def _cat_handler(node, logger):
    cat_args = CatArgs(*node.args, **node.kwargs)
    tensors = cat_args.tensors

    if any(QPARAM_KEY not in x.meta for x in tensors):
        return

    if QPARAM_KEY not in node.meta:
        return

    assert len(tensors) > 0
    in_dtype = qparam_dtype(tensors[0])
    if in_dtype == qparam_dtype(node):
        return

    if any(qparam_dtype(x) != in_dtype for x in tensors):
        return

    if in_dtype == "int16" and qparam_dtype(node) == "uint8":
        quantize = _insert_quantize_op_after(node)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        node.meta[QPARAM_KEY] = _u8_to_i16(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted after {node.name}.")
    else:
        raise NotYetSupportedError("Unsupported dtype")


def _bmm_handler(node, logger):
    bmm_args = BmmArgs(*node.args, **node.kwargs)
    x = bmm_args.input
    y = bmm_args.mat2

    if QPARAM_KEY not in x.meta:
        return
    if QPARAM_KEY not in y.meta:
        return
    if QPARAM_KEY not in node.meta:
        return

    if qparam_dtype(x) == qparam_dtype(node):
        return

    if qparam_dtype(x) == "int16" and qparam_dtype(node) == "uint8":
        quantize = _insert_quantize_op_after(node)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        node.meta[QPARAM_KEY] = _u8_to_i16(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted after {node.name}.")
    elif qparam_dtype(x) == "uint8" and qparam_dtype(node) == "int16":
        quantize = _insert_quantize_op_after(node)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        node.meta[QPARAM_KEY] = _i16_to_u8(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted after {node.name}.")
    else:
        raise NotYetSupportedError("Unsupported dtype")


def _permute_handler(node, logger):
    per_args = PermuteArgs(*node.args, **node.kwargs)
    inp = per_args.input

    if QPARAM_KEY not in inp.meta:
        return

    if QPARAM_KEY not in node.meta:
        return

    if qparam_dtype(inp) == qparam_dtype(node):
        return

    if qparam_dtype(inp) == "int16" and qparam_dtype(node) == "uint8":
        # A new Quantize Op (s16 to u8) is inserted before (not after)
        # permute Op to reduce tensor size ealier
        quantize = _insert_quantize_op_before(node, inp)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted before {node.name}.")
    elif qparam_dtype(inp) == "uint8" and qparam_dtype(node) == "int16":
        quantize = _insert_quantize_op_after(node)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        node.meta[QPARAM_KEY] = _i16_to_u8(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted after {node.name}.")
    else:
        raise NotYetSupportedError("Unsupported dtype")


def _reshape_handler(node, logger):
    reshape_args = ReshapeArgs(*node.args, **node.kwargs)
    inp = reshape_args.input

    if QPARAM_KEY not in inp.meta:
        return

    if QPARAM_KEY not in node.meta:
        return

    if qparam_dtype(inp) == qparam_dtype(node):
        return

    if qparam_dtype(inp) == "int16" and qparam_dtype(node) == "uint8":
        # A new Quantize Op (s16 to u8) is inserted before (not after)
        # reshape Op to reduce tensor size ealier
        quantize = _insert_quantize_op_before(node, inp)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted before {node.name}.")
    elif qparam_dtype(inp) == "uint8" and qparam_dtype(node) == "int16":
        quantize = _insert_quantize_op_after(node)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        node.meta[QPARAM_KEY] = _i16_to_u8(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted after {node.name}.")
    else:
        raise NotYetSupportedError("Unsupported dtype")


def _relu_handler(node, logger):
    relu_args = ReluArgs(*node.args, **node.kwargs)
    inp = relu_args.input

    if QPARAM_KEY not in inp.meta:
        return

    if QPARAM_KEY not in node.meta:
        return

    if qparam_dtype(inp) == qparam_dtype(node):
        return

    if qparam_dtype(inp) == "int16" and qparam_dtype(node) == "uint8":
        quantize = _insert_quantize_op_after(node)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        node.meta[QPARAM_KEY] = _u8_to_i16(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted after {node.name}.")
    elif qparam_dtype(inp) == "uint8" and qparam_dtype(node) == "int16":
        quantize = _insert_quantize_op_after(node)

        quantize.meta[QPARAM_KEY] = copy.deepcopy(node.meta[QPARAM_KEY])
        node.meta[QPARAM_KEY] = _i16_to_u8(node.meta[QPARAM_KEY])
        logger.debug(f"quantize_per_tensor.default is inserted after {node.name}.")
    else:
        raise NotYetSupportedError("Unsupported dtype")


_op_handler: defaultdict[Any, Any | None] = defaultdict(lambda: None)
_op_handler[torch.ops.aten.linear.default] = _linear_handler
_op_handler[torch.ops.aten.add.Tensor] = _add_handler
_op_handler[torch.ops.aten.mul.Tensor] = _mul_handler
_op_handler[torch.ops.aten.cat.default] = _cat_handler
_op_handler[torch.ops.aten.bmm.default] = _bmm_handler
_op_handler[torch.ops.aten.permute.default] = _permute_handler
_op_handler[torch.ops.aten.reshape.default] = _reshape_handler
_op_handler[torch.ops.aten.relu.default] = _relu_handler


@trace_graph_diff_on_pass
class InsertQuantizeOnDtypeMismatch(PassBase):
    """
    Insert quantize Op in the operators where circle's type inference is violated.
    Example. FullyConnected
    [BEFORE]
      Op (uint8) -  aten.linear.default (int16)
    [AFTER]
      Op (uint8) -  aten.linear.default (uint8) - quantized_decomposed.quantize_per_tensor.default (int16)
    Why is this pass necessary?
    - For some operators, circle's type inference pass overwrites the input's dtype to
    the output's dtype. For the above example, fully-connected layer (aten.linear.default)'s
    output dtype (int16) is updated to the input dtype (uint8), which breaks the semantics.
    This problem can occur in the tools (ex: circle2circle) that automatically apply type inference.
    - To resolve the issue, we insert quantize operators not to violate circle's type inference logic.
    - NOTE For some cases, Quantize Op is inserted before the operators.

    Let's assume Reshape Op's input is int16 and output is uint8. There are two possible places to insert
    Quantize Op.

    1. Insert Quantize before Reshape.

    ```
    Predecessor (int16)-> Quantize (uint8) -> Reshape (uint8) -> ...
    ```

    2. Insert Quantize after Reshape.

    ```
    Predecessor (int16)-> Reshape (int16) -> Quantize (uint8) -> ...
    ```

    Comparing 1) and 2), the difference is that Reshape operation is conducted in uint8 or int16.
    We go with 1), which does Reshape in uint8, for faster execution. Note that Reshape Op does not
    change the value, so its dytpe does not affect accuracy.
    """

    def __init__(self):
        super().__init__()

    def call(self, exported_program: ExportedProgram) -> PassResult:
        logger = logging.getLogger(__name__)

        graph_module = exported_program.graph_module
        graph: torch.fx.Graph = graph_module.graph

        for node in graph.nodes:
            if node.op != "call_function":
                continue

            handler = _op_handler[node.target]
            if handler is not None:
                handler(node, logger)

        graph.eliminate_dead_code()
        graph.lint()
        graph_module.recompile()

        # Run only once.
        return PassResult(False)
