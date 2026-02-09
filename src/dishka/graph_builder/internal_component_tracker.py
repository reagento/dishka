from collections import defaultdict
from itertools import count
from typing import Any

from dishka.entities.component import Component
from dishka.entities.key import DependencyKey


class InternalComponentTracker:
    def __init__(self):
        self.depth: dict[tuple[Any, Component], count] = defaultdict(count)

    def to_internal_component(self, prefix: str, provides: DependencyKey):
        return DependencyKey(
            provides.type_hint,
            provides.component,
            next(self.depth[provides.type_hint, provides.component]) + 1,
        )