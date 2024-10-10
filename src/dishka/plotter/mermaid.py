import re

from dishka.plotter.model import Group, Node, NodeType, Renderer

HTML_TEMPLATE = """\
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>

<pre class="mermaid">
{diagram}
</pre>

<script type="module">
    import mermaid
    from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize(config);
</script>
</body>
</html>

"""


class MermaidRenderer(Renderer):
    def __init__(self):
        self.names: dict[str, str] = {}

    def _render_node(self, node: Node) -> str:
        name = self._node_type(node) + self._escape(node.name)
        return (
            f'class {node.id}["{name}"]'
            + "{\n"
            + ((f"    {node.source_name}()\n") if node.source_name else " \n")
            + "".join(
                f"    {self.names[dep]}\n" for dep in node.dependencies
            )
            + "}\n"
        )

    def _escape(self, line: str) -> str:
        return re.sub(r"[^\w_.\-]", "_", line)

    def _render_node_deps(self, node: Node) -> list[str]:
        return [
            f"{dep} ..> {node.id}"
            for dep in node.dependencies
        ]

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
        if not group.nodes and not group.children:
            return ""
        name = name_prefix + self._escape(group.name or "")
        res = ""
        if group.nodes:
            res = f"namespace {name} {{\n"
            for node in group.nodes:
                res += self._render_node(node) + "\n"
            res += "}\n"
        for child in group.children:
            res += self._render_group(child,  name) + "\n"
        return res

    def _render_links(self, group: Group) -> str:
        res = ""
        for node in group.nodes:
            for dep_str in self._render_node_deps(node):
                res += dep_str + "\n"
        for child in group.children:
            res += self._render_links(child)
        return res

    def _fill_names(self, groups: list[Group]) -> None:
        for group in groups:
            for node in group.nodes:
                self.names[node.id] = node.name
            self._fill_names(group.children)

    def render(self, groups: list[Group]) -> str:
        self._fill_names(groups)

        res = "classDiagram\n"
        res += "direction LR\n"
        for group in groups:
            res += self._render_group(group)
            res += self._render_links(group)
        return HTML_TEMPLATE.format(diagram=res)
