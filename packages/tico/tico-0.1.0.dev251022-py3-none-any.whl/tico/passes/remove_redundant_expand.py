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

from torch.export import ExportedProgram

from tico.passes import ops
from tico.serialize.circle_mapping import extract_shape
from tico.utils import logging
from tico.utils.passes import PassBase, PassResult
from tico.utils.trace_decorators import trace_graph_diff_on_pass
from tico.utils.utils import is_target_node
from tico.utils.validate_args_kwargs import ExpandArgs


@trace_graph_diff_on_pass
class RemoveRedundantExpand(PassBase):
    """
    This pass removes redundant `aten.expand` operators where shapes of input and output are same.
    """

    def __init__(self):
        super().__init__()

    def call(self, exported_program: ExportedProgram) -> PassResult:
        logger = logging.getLogger(__name__)

        graph_module = exported_program.graph_module
        graph = graph_module.graph
        modified = False
        for node in graph.nodes:
            if not is_target_node(node, ops.aten.expand):
                continue

            args = ExpandArgs(*node.args, **node.kwargs)  # type: ignore[arg-type]
            input, size = args.input, args.size

            input_shape = extract_shape(input)
            output_shape = extract_shape(node)

            if input_shape != output_shape:
                continue

            node.replace_all_uses_with(input, propagate_meta=False)

            modified = True
            logger.debug(f"{node.name} is replaced with {input.name}")

        graph.eliminate_dead_code()
        graph.lint()
        graph_module.recompile()

        return PassResult(modified)
