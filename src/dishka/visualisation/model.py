from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Protocol


class GroupType(Enum):
    SCOPE = "SCOPE"
    COMPONENT = "COMPONENT"

class NodeType(Enum):
    CONTEXT = "Context"
    FACTORY = "Factory"
    ALIAS = "Alias"

@dataclass
class Node:
    id: str
    name: str
    dependencies: list[str]
    type: NodeType

@dataclass
class Group:
    id: str
    name: str
    children: List['Group']
    nodes: list[Node]
    type: GroupType


class Renderer(Protocol):
    @abstractmethod
    def render(self, groups: list[Group]) -> str:
        raise NotImplementedError
