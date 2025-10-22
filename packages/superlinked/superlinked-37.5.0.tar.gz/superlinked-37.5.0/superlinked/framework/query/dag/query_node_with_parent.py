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

import asyncio
from abc import abstractmethod

from beartype.typing import Generic, Mapping, Sequence
from typing_extensions import override

from superlinked.framework.common.dag.context import ExecutionContext
from superlinked.framework.common.dag.node import NT
from superlinked.framework.common.exception import InvalidStateException
from superlinked.framework.query.dag.query_evaluation_data_types import (
    QueryEvaluationResult,
    QueryEvaluationResultT,
)
from superlinked.framework.query.dag.query_node import QueryNode
from superlinked.framework.query.query_node_input import QueryNodeInput


class QueryNodeWithParent(QueryNode[NT, QueryEvaluationResultT], Generic[NT, QueryEvaluationResultT]):
    @override
    async def _evaluate(
        self,
        inputs: Mapping[str, Sequence[QueryNodeInput]],
        context: ExecutionContext,
    ) -> QueryEvaluationResult[QueryEvaluationResultT]:
        propagated_inputs = self._propagate_inputs_to_invert(inputs, context)
        parent_results = await self._evaluate_parents(propagated_inputs, context)
        self._validate_parent_results(parent_results)
        return self._evaluate_parent_results(parent_results, context)

    def _propagate_inputs_to_invert(
        self,
        inputs: Mapping[str, Sequence[QueryNodeInput]],
        context: ExecutionContext,  # pylint: disable=unused-argument
    ) -> dict[str, Sequence[QueryNodeInput]]:
        inputs_to_invert = [input_ for input_ in inputs.get(self.node_id, []) if input_.to_invert]
        if inputs_to_invert:
            if len(self.parents) > 1:
                raise InvalidStateException(
                    "Addressed query node with inputs needing to be inverted is prohibited.",
                    node_id=self.node_id,
                    node_type=type(self).__name__,
                    inputs_to_invert=inputs_to_invert,
                )
            if len(self.parents) == 1:
                return self._merge_inputs([inputs, {self.parents[0].node_id: inputs_to_invert}])
        return dict(inputs)

    async def _evaluate_parents(
        self, inputs: Mapping[str, Sequence[QueryNodeInput]], context: ExecutionContext
    ) -> Sequence[QueryEvaluationResult]:
        return await asyncio.gather(*[parent.evaluate_with_validation(inputs, context) for parent in self.parents])

    def _validate_parent_results(self, parent_results: Sequence[QueryEvaluationResult]) -> None:
        if len(parent_results) != len(self.parents):
            raise InvalidStateException(
                "Mismatching number of parents and parent results.",
                node_id=self.node_id,
                node_type=type(self).__name__,
                parents_count=len(self.parents),
                parent_results_count=len(parent_results),
            )

    @abstractmethod
    def _evaluate_parent_results(
        self, parent_results: Sequence[QueryEvaluationResult], context: ExecutionContext
    ) -> QueryEvaluationResult[QueryEvaluationResultT]:
        pass
