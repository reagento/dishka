from collections.abc import Sequence
from typing import NamedTuple

from dishka.entities.component import Component
from dishka.entities.factory_type import FactoryData, FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from dishka.text_rendering import get_name


class PathRenderer:
    def __init__(self, cycle: bool):
        self.cycle = cycle

    def _arrow_cycle(self, index: int, length: int) -> str:
        if length == 1:
            return "⥁ "
        elif index == 0:
            return "╭─▷─╮ "
        elif index + 1 < length:
            # if index % 2:
            #     return "│   │ "
            return "│   ▼ "
        else:
            return "╰─◁─╯ "

    def _arrow_line(self, index: int, length: int) -> str:
        if index + 1 < length:
            return "▼   "
        else:
            return "╰─▷ "

    def _arrow(self, index: int, length: int):
        if self.cycle:
            return self._arrow_cycle(index, length)
        return self._arrow_line(index, length)

    def _right_arrow(self, index: int, length: int):
        if self.cycle:
            return ""
        #return ""
        if index + 1 < length:
            return "  │"
        return "◁─╯"

    def _switch_arrow(self, index: int, length: int):
        if self.cycle:
            if index> 0:
                # return "│   │ "
                return "│   │ "
            return "      "
        #return "│"
        if index==0:
            return "├───"
        return "├───"

    def _switch_right_arrow(self, index: int, length: int):
        if self.cycle:
            return ""
        #return ""
        if index==0:
            return "──┤"
        return "──┤"

    def _switch_filler(self):
        if self.cycle:
            return " "
        #return " "
        return "─"

    def _key(self, key: DependencyKey) -> str:
        return get_name(key.type_hint, include_module=True)

    def _source(self, factory: FactoryData) -> str:
        source = factory.source
        if source == factory.provides.type_hint:
            return ""
        if factory.type is FactoryType.ALIAS:
            return "alias"

        return get_name(source, include_module=False)

    def _switch(
            self, scope: BaseScope | None, component: Component | None,
    ) -> str:
        # if self.cycle:
        return f"◈ component={component!r}, {scope} ◈"
        return f"[ component={component!r}, {scope} ]"

    def render(
            self,
            path: Sequence[FactoryData],
            last: DependencyKey | None = None,
    ) -> str:
        row_count = len(path) + bool(last)
        # each row is: num, arrow, col1, col2, arrow, dest{scope, component}
        rows = [
            Row(
                row_num,
                self._arrow(row_num, row_count),
                [self._key(factory.provides), self._source(factory)],
                self._right_arrow(row_num, row_count),
                (factory.scope, factory.provides.component)
            )
            for row_num, factory in enumerate(path)
        ]
        if last:
            rows.append(
                Row(
                    row_count - 1,
                    self._arrow(row_count-1, row_count),
                    [self._key(last), "???"],
                    self._right_arrow(row_count-1, row_count),
                    (rows[-1].dest[0], last.component),
                )
            )
        prev_dest: tuple[BaseScope | None, Component | None] = (None, "")
        space_left = "   "
        space_columns = "   "
        res = ""

        columns_count = len(rows[0].columns)
        columns_width = [
            max(len(row.columns[col_num]) for row in rows)
            for col_num in range(columns_count)
        ]
        total_width = (
            len(space_left) +
            len(rows[0].border_left) +  # left borders are equal length
            sum(columns_width) +
            len(space_columns) * (columns_count - 1) +
            len(rows[0].border_right) # right borders are equal length
        )
        switch_len = sum(columns_width) + len(space_columns) * (columns_count - 1)
        for row in rows:
            if row.dest != prev_dest:
                res += (
                    space_left +
                    self._switch_arrow(row.num, row_count) +
                    self._switch(*row.dest).center(
                        switch_len, self._switch_filler()
                    ) +
                    self._switch_right_arrow(row.num, row_count) +
                    "\n"
                )
                prev_dest = row.dest
            res += (
                space_left +
                row.border_left +
                space_columns.join(
                    c.ljust(cw)
                    for c, cw in zip(row.columns, columns_width)
                ) +
                row.border_right +
                "\n"
            )
        return res


class Row(NamedTuple):
    num: int
    border_left: str
    columns: Sequence[str]
    border_right: str
    dest: tuple[BaseScope | None, Component | None]