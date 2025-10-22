# Copyright 2024 Superlinked, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from beartype.typing import Mapping, Sequence
from typing_extensions import override

from superlinked.framework.common.dag.context import ExecutionContext
from superlinked.framework.common.dag.index_node import IndexNode
from superlinked.framework.common.dag.node import Node
from superlinked.framework.common.data_types import Vector
from superlinked.framework.common.exception import InvalidStateException
from superlinked.framework.query.dag.query_evaluation_data_types import (
    QueryEvaluationResult,
)
from superlinked.framework.query.dag.query_node import QueryNode
from superlinked.framework.query.dag.query_node_with_parent import QueryNodeWithParent
from superlinked.framework.query.query_node_input import QueryNodeInput

QUERIED_SCHEMA_NAME_CONTEXT_KEY = "queried_schema_name"


class QueryIndexNode(QueryNodeWithParent[IndexNode, Vector]):
    def __init__(
        self,
        node: IndexNode,
        parents: Sequence[QueryNodeWithParent[Node[Vector], Vector]],
    ) -> None:
        super().__init__(node, parents)

    @override
    def _validate_evaluation_inputs(self, inputs: Mapping[str, Sequence[QueryNodeInput]]) -> None:
        super()._validate_evaluation_inputs(inputs)
        if invalid_index_node_inputs := [input_ for input_ in inputs.get(self.node_id, []) if not input_.to_invert]:
            raise InvalidStateException(
                "Query index node can only be addressed with items to be inverted.",
                node_inputs=invalid_index_node_inputs,
            )

    @override
    def _propagate_inputs_to_invert(
        self, inputs: Mapping[str, Sequence[QueryNodeInput]], context: ExecutionContext
    ) -> dict[str, Sequence[QueryNodeInput]]:
        inputs_to_invert = [input_ for input_ in inputs.get(self.node_id, []) if input_.to_invert]
        if inputs_to_invert:
            active_parent = self._get_active_parent(context)
            return self._merge_inputs([inputs, {active_parent.node_id: inputs_to_invert}])
        return dict(inputs)

    @override
    async def _evaluate_parents(
        self, inputs: Mapping[str, Sequence[QueryNodeInput]], context: ExecutionContext
    ) -> list[QueryEvaluationResult[Vector]]:
        active_parent = self._get_active_parent(context)
        return [await active_parent.evaluate_with_validation(inputs, context)]

    @override
    def _validate_parent_results(self, parent_results: Sequence[QueryEvaluationResult]) -> None:
        if len(parent_results) != 1:
            raise InvalidStateException(f"{type(self).__name__} must have exactly 1 parent result.")

    @override
    def _evaluate_parent_results(
        self,
        parent_results: Sequence[QueryEvaluationResult],
        context: ExecutionContext,
    ) -> QueryEvaluationResult[Vector]:
        if (count := len(parent_results)) != 1:
            raise InvalidStateException("Query index must receive exactly 1 parent result.", count=count)
        if not isinstance(parent_results[0].value, Vector):
            raise InvalidStateException(
                "Query index's parent result must be a vector.",
                parent_result_type=type(parent_results[0].value).__name__,
            )
        return parent_results[0]

    @override
    def _validate_get_vector_parts_inputs(self, vectors: Sequence[Vector]) -> None:
        self._validate_vectors_dimension(self.node.length, vectors)

    @override
    def _get_vector_parts(
        self, vectors: Sequence[Vector], node_ids: Sequence[str], context: ExecutionContext
    ) -> list[list[Vector]] | None:
        parent = self._get_active_parent(context)
        return parent.get_vector_parts(vectors, node_ids, context)

    def _get_active_parent(self, context: ExecutionContext) -> QueryNode[Node[Vector], Vector]:
        queried_schema_name = context.get_node_context_value(self.node_id, QUERIED_SCHEMA_NAME_CONTEXT_KEY, str)
        if queried_schema_name is None:
            raise InvalidStateException("Missing schema name for query.")
        active_parents = [
            parent
            for parent in self.parents
            if queried_schema_name in [schema._schema_name for schema in parent.node.schemas]
        ]
        if len(active_parents) == 0:
            raise InvalidStateException("Query dag doesn't have the given schema.", schema_name=queried_schema_name)
        if len(active_parents) > 1:
            raise InvalidStateException(
                "Ambiguous query dag definition, query index node cannot have parents having the same schema.",
                schema_name=queried_schema_name,
            )
        return active_parents[0]
