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

from dataclasses import dataclass

from beartype.typing import Generic, Sequence

from superlinked.framework.common.schema.id_schema_object import IdSchemaObject
from superlinked.framework.common.space.config.aggregation.aggregation_config import (
    AggregationInputT,
)
from superlinked.framework.common.space.config.embedding.embedding_config import (
    EmbeddingInputT,
)
from superlinked.framework.dsl.index.util.effect_with_referenced_schema_object import (
    EffectWithReferencedSchemaObject,
)
from superlinked.framework.dsl.space.space import Space


@dataclass(frozen=True)
class AggregationEffectGroup(Generic[AggregationInputT, EmbeddingInputT]):
    """
    Group of effects with the same space and affected schema.
    """

    space: Space[AggregationInputT, EmbeddingInputT]
    affected_schema: IdSchemaObject
    effects: Sequence[EffectWithReferencedSchemaObject[AggregationInputT, EmbeddingInputT]]
