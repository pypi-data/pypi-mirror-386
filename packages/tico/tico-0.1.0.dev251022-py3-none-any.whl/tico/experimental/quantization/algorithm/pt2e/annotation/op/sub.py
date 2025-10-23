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

from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import torch.fx
import torch

import tico.experimental.quantization.algorithm.pt2e.annotation.spec as annot_spec
import tico.experimental.quantization.algorithm.pt2e.annotation.utils as annot_utils
import tico.experimental.quantization.algorithm.pt2e.utils as quant_utils
from tico.experimental.quantization.algorithm.pt2e.annotation.config import (
    QuantizationConfig,
)
from tico.utils.validate_args_kwargs import SubTensorArgs


@annot_spec.register_annotator([torch.ops.aten.sub.Tensor])
def _annotate_sub(
    gm: torch.fx.GraphModule,
    node: torch.fx.Node,
    quantization_config: Optional[QuantizationConfig],
    filter_fn: Optional[Callable[[torch.fx.Node], bool]] = None,
):
    if node.op != "call_function" or node.target != torch.ops.aten.sub.Tensor:
        return
    if filter_fn and not filter_fn(node):
        return
    if quant_utils.is_annotated(node):
        return

    args = SubTensorArgs(*node.args)  # type: ignore[arg-type]
    input = args.input
    other = args.other

    input_act_qspec = quant_utils.get_input_act_qspec(quantization_config)
    if isinstance(input, torch.fx.Node):
        annot_utils.annotate_input_qspec_map(node, input, input_act_qspec)
    if isinstance(other, torch.fx.Node):
        annot_utils.annotate_input_qspec_map(node, other, input_act_qspec)

    output_act_qspec = quant_utils.get_output_act_qspec(quantization_config)
    annot_utils.annotate_output_qspec(node, output_act_qspec)

    annot_utils.mark_nodes_as_annotated(node)
