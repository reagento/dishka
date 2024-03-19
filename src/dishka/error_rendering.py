from collections.abc import Sequence

from dishka.dependency_source import Factory, FactoryType
from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope


class PathRenderer:

    def _arrow_cycle(self, index: int, length: int) -> str:
        if length == 1:
            return "⥁"
        elif index == 0:
            return " → → "
        elif index + 1 < length:
            return "↑   ↓"
        else:
            return " ← ← "

    def _arrow_line(self, index: int, length: int) -> str:
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

    def _switch(
            self, scope: BaseScope, component: Component,
    ) -> str:
        return f"~~~ component={component!r}, {scope} ~~~\n"

    def render(
            self,
            path: Sequence[Factory],
            last: DependencyKey | None = None,
    ):
        if last is None:
            _arrow = self._arrow_cycle
        else:
            _arrow = self._arrow_line

        width = max(len(self._key(x.provides)) for x in path)
        if last:
            width = max(width, len(self._key(last)))

        dest = None
        length = len(path) + bool(last)

        res = ""
        for i, factory in enumerate(path):
            arrow = _arrow(i, length)
            new_dest = (factory.scope, factory.provides.component)
            if new_dest != dest:
                res += "   " + " " * len(arrow) + " " + self._switch(*new_dest)
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
            arrow = _arrow(length + 1, length)
            if new_dest != dest:
                res += "   " + " " * len(arrow) + " " + self._switch(*new_dest)
                dest = new_dest
            res += (
                    "   " + arrow + " " +
                    self._key(last).ljust(width) +
                    " ???\n"
            )
        return res
