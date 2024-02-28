from collections.abc import Sequence

from dishka.dependency_source import Factory, FactoryType
from dishka.entities.key import DependencyKey


class PathRenderer:

    def _arrow(self, index: int, length: int, cycle_mode: bool) -> str:
        if cycle_mode:
            if index == 0:
                if length == 1:
                    return "⥁"
                else:
                    return " → → "
            elif index + 1 < length:
                return "↑   ↓"
            else:
                return " ← ← "
        else:
            if index + 1 < length:
                return "↓ "
            else:
                return " →"

    def _key(self, key: DependencyKey) -> str:
        return str(key.type_hint)

    def _source(self, factory: Factory) -> str:
        source = factory.source
        if source == factory.provides.type_hint:
            return ""
        if factory.type is FactoryType.ALIAS:
            return "alias"
        if func := getattr(source, "__func__", None):
            return getattr(func, "__qualname__", None) or str(func)
        else:
            return str(source)

    def render(self, path: Sequence[Factory], last: DependencyKey = None):
        print(path, last)
        cycle = last is None

        width = max(len(self._key(x.provides)) for x in path)
        if last:
            width = max(width, len(self._key(last)))

        dest = None
        length = len(path) + bool(last)

        res = ""
        for i, factory in enumerate(path):
            arrow = self._arrow(i, length, cycle)
            new_dest = (factory.scope, factory.provides.component)
            if new_dest != dest:
                res += (
                        "   " + " " * len(arrow) + " " +
                        f"=== component={new_dest[1]!r}, {new_dest[0]} ===\n"
                )
                dest = new_dest

            res += (
                    "   " + arrow + " " +
                    self._key(factory.provides).ljust(width) +
                    " " +
                    self._source(factory) +
                    "\n"
            )
        if last:
            new_dest = (dest[0], last.component)
            if new_dest != dest:
                res += (
                        "   " + " " * len(arrow) + " " +
                        f"=== component={new_dest[1]!r}, {new_dest[0]} ===\n"
                )
                dest = new_dest
            arrow = self._arrow(length + 1, length, cycle)
            res += (
                    "   " + arrow + " " +
                    self._key(last).ljust(width) +
                    " ???"
            )
        return res
