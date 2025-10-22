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

from superlinked.framework.common.dag.index_node import IndexNode
from superlinked.framework.common.dag.node import Node
from superlinked.framework.common.exception import InvalidStateException
from superlinked.framework.common.schema.id_schema_object import IdSchemaObject


class SchemaDag:
    """
    Represents a `Dag`'s projection to a particular schema. Must have exactly 1 leaf `Node` of type `IndexNode`.
    """

    def __init__(self, schema: IdSchemaObject, nodes: list[Node]) -> None:
        self.__validate(nodes)
        self.__schema = schema
        self.__nodes = nodes

    @property
    def schema(self) -> IdSchemaObject:
        return self.__schema

    @property
    def nodes(self) -> list[Node]:
        return self.__nodes

    def __validate(self, nodes: list[Node]) -> None:
        class_name = type(self).__name__
        leaf_nodes = [node for node in nodes if len(node.children) == 0]
        if len(leaf_nodes) != 1:
            raise InvalidStateException(f"{class_name} must have exactly one leaf Node.", n_leaf_nodes=len(leaf_nodes))
        if not isinstance(leaf_nodes[0], IndexNode):
            raise InvalidStateException(f"{class_name} must have a IndexNode leaf Node.")
