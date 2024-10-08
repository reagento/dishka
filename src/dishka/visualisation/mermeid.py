from dishka.visualisation.model import Renderer, Group, Node, NodeType, \
    GroupType


class MermeidRenderer(Renderer):
    def _render_node(self, node: Node) -> str:
        name = self._node_type(node) + node.name
        return f"class {node.id}[\"{name}\"]"

    def _render_node_deps(self, node: Node) -> list[str]:
        return [
            f"{dep} ..> {node.id}"
            for dep in node.dependencies
        ]

    def _group_type(self, group: Group) -> str:
        return ""

    def _node_type(self, node: Node) -> str:
        if node.type is NodeType.CONTEXT:
            return "📥 "
        elif node.type is NodeType.ALIAS:
            return "🔗 "
        return "🏭 "

    def _render_group(
            self, group: Group, indent: str = "", name_prefix: str = "",
    ) -> str:
        name = self._group_type(group) + name_prefix + (group.name or '')
        res = ""
        if group.nodes:
            res = f"{indent}namespace {name} {{\n"
            for node in group.nodes:
                res += indent + "    " + self._render_node(node) + "\n"
            res += indent + "}\n"
        for child in group.children:
            res += self._render_group(child, indent, name) + "\n"
        return res

    def _render_links(self, group: Group) -> str:
        res = ""
        for node in group.nodes:
            for dep_str in self._render_node_deps(node):
                res += dep_str + "\n"
        for child in group.children:
            res += self._render_links(child)
        return res

    def render(self, groups: list[Group]) -> str:
        res = "classDiagram\n"
        for group in groups:
            res += self._render_group(group)
            res += self._render_links(group)
        return res
