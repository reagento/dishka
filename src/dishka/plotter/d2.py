import re

from dishka.plotter.model import Group, Node, NodeType, Renderer


class D2Renderer(Renderer):
    def __init__(self):
        self.names: dict[str, str] = {}
        self.full_ids: dict[str, str] = {}

    def _escape(self, line: str) -> str:
        return re.sub(r"[^\w_.\-]", "_", line)

    def _render_node(self, node: Node) -> str:
        name = self._node_type(node) + self._escape(node.name)
        if node.source_name:
            source = f'    "{self._escape(node.source_name)}()": ""\n'
        else:
            source = ""

        res = f'{node.id}: "{name}"' + "{\n"
        res += "    shape: class\n"
        res += source
        for dep in node.dependencies:
            dep_name = self._escape(self.names[dep])
            res += f"    {dep_name}\n"
        res += "}\n"
        return res

    def _render_node_deps(self, node: Node) -> list[str]:
        return [
            f"{self.full_ids[dep]} --> {self.full_ids[node.id]}"
            for dep in node.dependencies
        ]

    def _group_type(self, group: Group) -> str:
        return ""

    def _node_type(self, node: Node) -> str:
        if node.is_protocol:
            prefix = "Ⓘ "
        else:
            prefix = ""
        if node.type is NodeType.CONTEXT:
            return "📥 " + prefix
        elif node.type is NodeType.ALIAS:
            return "🔗 " + prefix
        return "🏭 " + prefix

    def _render_group(
            self, group: Group, name_prefix: str = "",
    ) -> str:
        name = (
            self._group_type(group)
            + name_prefix
            + self._escape(group.name or "")
        )
        res = f'{group.id}: "{name}"' + "{\n"
        for node in group.nodes:
            res += self._render_node(node) + "\n"
        for child in group.children:
            res += self._render_group(child, name) + "\n"
        res += "}\n"
        return res

    def _render_links(self, group: Group) -> str:
        res = ""
        for node in group.nodes:
            for dep_str in self._render_node_deps(node):
                res += dep_str + "\n"
        for child in group.children:
            res += self._render_links(child)
        return res

    def _fill_names(self, groups: list[Group], prefix: str = "") -> None:
        for group in groups:
            if prefix:
                id_prefix = prefix + "." + group.id
            else:
                id_prefix = group.id
            self.full_ids[group.id] = id_prefix
            for node in group.nodes:
                self.names[node.id] = node.name
                self.full_ids[node.id] = id_prefix + "." + node.id
            self._fill_names(group.children, prefix=id_prefix)

    def render(self, groups: list[Group]) -> str:
        self._fill_names(groups)

        res = ""
        for group in groups:
            res += self._render_group(group)
            res += self._render_links(group)
        return res
