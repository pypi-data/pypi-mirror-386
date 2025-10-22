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

from beartype.typing import Any, Generic
from typing_extensions import override

from superlinked.framework.common.dag.node import Node
from superlinked.framework.common.schema.schema_object import SFT, SchemaField


class SchemaFieldNode(Generic[SFT], Node[SFT]):
    def __init__(self, schema_field: SchemaField[SFT]) -> None:
        super().__init__(schema_field.type_, [], schemas={schema_field.schema_obj})
        self.schema_field = schema_field

    @override
    def _get_node_id_parameters(self) -> dict[str, Any]:
        return {"schema": self.schema_field.schema_obj._schema_name, "schema_field": self.schema_field.name}
