import linecache
import re
from textwrap import indent
from typing import Any, Sequence, Mapping

from .container_objects import Exit
from .entities.factory_type import FactoryType, FactoryData
from .entities.key import DependencyKey
from .entities.scope import BaseScope
from .exceptions import NoContextValueError, UnsupportedFactoryError
from .text_rendering import get_name


class Node(FactoryData):
    __slots__ = (
        "dependencies",
        "kw_dependencies",
        "cache",
    )

    def __init__(
            self,
            *,
            dependencies: Sequence["Node"],
            kw_dependencies: Mapping[str, "Node"],
            source: Any,
            provides: DependencyKey,
            scope: BaseScope,
            type_: FactoryType | None,
            cache: bool,
    ) -> None:
        super().__init__(
            source=source,
            provides=provides,
            type_=type_,
            scope=scope,
        )
        self.dependencies = dependencies
        self.kw_dependencies = kw_dependencies
        self.cache = cache


def make_args(args: list[str], kwargs: dict[str, str]) -> str:
    res = ", ".join(args)
    if not kwargs:
        return res
    if res:
        res += ", "
    res += ", ".join(
        f"{arg}={var}"
        for arg, var in kwargs
    )
    return res


GENERATOR = """
generator = {source}({args})
{var} = next(generator)
exits.append(Exit(factory_type, generator))
"""
ASYNC_GENERATOR = """
generator = {source}({args})
{var} = await anext(generator)
exits.append(Exit(factory_type, generator))
"""
FACTORY = """
{var} = {source}({args})
"""
ASYNC_FACTORY = """
{var} = await {source}({args})
"""
VALUE = """
{var} = {source}
"""
ALIAS = """
{var} = {args}
"""
CONTEXT = """
raise NoContextValueError({key})
"""
INVALID = """
raise UnsupportedFactoryError(
    f"Unsupported factory type {{factory_type}}.",
)
"""
GO_PARENT = """
{var} = getter({key})
"""
GO_PARENT_ASYNC = """
{var} = await getter({key})
"""

ASYNC_BODIES = {
    FactoryType.ASYNC_FACTORY: ASYNC_FACTORY,
    FactoryType.FACTORY: FACTORY,
    FactoryType.ASYNC_GENERATOR: ASYNC_GENERATOR,
    FactoryType.GENERATOR: GENERATOR,
    FactoryType.VALUE: VALUE,
    FactoryType.CONTEXT: CONTEXT,
    FactoryType.ALIAS: ALIAS,
    None: GO_PARENT_ASYNC,
}
SYNC_BODIES = {
    FactoryType.FACTORY: FACTORY,
    FactoryType.GENERATOR: GENERATOR,
    FactoryType.VALUE: VALUE,
    FactoryType.CONTEXT: CONTEXT,
    FactoryType.ALIAS: ALIAS,
    None: GO_PARENT,
}
FUNC_TEMPLATE = """
{async_}def {func_name}(getter, exits, context):
    cache_getter = context.get
    {body}
    return {var}
"""

IF_TEMPLATE = """
if {var} := cache_getter({key}, None):
    pass  # cache found
else:
    {deps}
    {body}
    {cache}
"""
CACHE = "context[{key}] = {var}"


def make_name(obj: Any, ns: dict[Any, str]) -> str:
    if isinstance(obj, DependencyKey):
        key = get_name(obj.type_hint, include_module=False) + obj.component
    else:
        key = get_name(obj, include_module=False)
    key = re.sub(r"\W", "_", key)
    if key in ns:
        key += f"_{len(ns)}"
    return key


def make_globals(node: Node, ns: dict[Any, str]):
    if node.provides not in ns:
        ns[node.provides] = make_name(node.provides, ns)
    if node.source not in ns:
        ns[node.source] = make_name(node.source, ns)
    for dep in node.dependencies:
        make_globals(dep, ns)
    for dep in node.kw_dependencies.values():
        make_globals(dep, ns)


def make_var(node: Node, ns: dict[Any, str]):
    return "value_" + ns[node.provides].lower()


def make_if(node: Node, node_var: str, ns: dict[Any, str],
            is_async: bool) -> str:
    node_key = ns[node.provides]
    node_source = ns[node.source]

    deps = "".join(
        make_if(dep, make_var(dep, ns), ns, is_async)
        for dep in node.dependencies
    )
    deps += "".join(
        make_if(dep, make_var(dep, ns), ns, is_async)
        for dep in node.kw_dependencies.values()
    )
    deps = indent(deps, "    ")
    if node.cache:
        cache = CACHE.format(var=node_var, key=node_key)
    else:
        cache = "# no cache"

    args = [make_var(dep, ns) for dep in node.dependencies]
    kwargs = {
        key: make_var(dep, ns)
        for key, dep in node.kw_dependencies.items()
    }

    if is_async:
        body_template = ASYNC_BODIES.get(node.type, INVALID)
    else:
        body_template = SYNC_BODIES.get(node.type, INVALID)

    args_str = make_args(args, kwargs)
    body_str = body_template.format(
        source=node_source,
        key=node_key,
        var=node_var,
        args=args_str,
    )
    body_str = indent(body_str, "    ")

    return IF_TEMPLATE.format(
        var=node_var,
        key=node_key,
        deps=deps,
        body=body_str,
        cache=cache,
    )


def make_func(
        node: Node, ns: dict[Any, str], func_name: str, is_async: bool,
) -> str:
    node_var = make_var(node, ns)
    body = make_if(node, node_var, ns, is_async)
    body = indent(body, "    ")
    return FUNC_TEMPLATE.format(
        async_="async " if is_async else "",
        var=node_var,
        body=body,
        func_name=func_name,
    )


def compile_graph(node: Node, is_async: bool):
    ns: dict[Any, str] = {
        node.type: "factory_type",
        Exit: "Exit",
        NoContextValueError: "NoContextValueError",
        UnsupportedFactoryError: "UnsupportedFactoryError",
    }
    make_globals(node, ns)
    func_name = f"get_{ns[node.provides].lower()}"
    src = make_func(node, ns, func_name, is_async=is_async)
    src = "\n".join(line for line in src.splitlines() if line.strip())

    print(src)
    print()
    source_file_name = f"__dishka_factory_{id(node.provides)}"
    if is_async:
        source_file_name += "_async"
    lines = src.splitlines(keepends=True)
    linecache.cache[source_file_name] = (
        len(src), None, lines, source_file_name,
    )
    global_ns = {value: key for key, value in ns.items()}
    exec(src, global_ns)
    return global_ns[func_name]
