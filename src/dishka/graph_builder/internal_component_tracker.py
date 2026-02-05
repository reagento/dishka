from collections import defaultdict
from itertools import count

from dishka.entities.key import DependencyKey


class InternalComponentTracker:
    def __init__(self):
        self.depth: dict[tuple[DependencyKey, str], count] = defaultdict(count)


    def to_internal_component(self, prefix: str, provides: DependencyKey):
        depth = next(self.depth[provides, prefix])
        new_component = f"{prefix}{depth}_{provides.component}"
        return DependencyKey(provides.type_hint, new_component)
