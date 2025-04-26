from collections.abc import Sequence

from dishka.entities.component import Component
from dishka.entities.factory_type import FactoryData
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from dishka.text_rendering.name import get_key_name, get_source_name


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

    def _switch(
            self, scope: BaseScope | None, component: Component | None,
    ) -> str:
        return f"~~~ component={component!r}, {scope} ~~~\n"

    def render(
            self,
            path: Sequence[FactoryData],
            last: DependencyKey | None = None,
    ) -> str:
        if last is None:
            _arrow = self._arrow_cycle
        else:
            _arrow = self._arrow_line

        width = max(len(get_key_name(x.provides)) for x in path)
        if last:
            width = max(width, len(get_key_name(last)))
        width += 2  # add spacing between columns

        dest: tuple[BaseScope | None, Component | None] = (None, "")
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
                    get_key_name(factory.provides).ljust(width) +
                    " " +
                    get_source_name(factory) +
                    "\n"
            )
        if last:
            new_dest = (dest[0], last.component)
            arrow = _arrow(length + 1, length)
            if new_dest != dest:
                res += "   " + " " * len(arrow) + " " + self._switch(*new_dest)
            res += (
                    "   " + arrow + " " +
                    get_key_name(last).ljust(width) +
                    " ???\n"
            )
        return res
