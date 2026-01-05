"""
Compile call of factory according to its type

For each template we expect global variables:
* source - factory.source
* factory_type - factory.type
* provides - factory.provides
* Exit
* NoContextValueError
* UnsupportedFactoryError

When formatting substituted:
* await - "await " for async container or empty string
* async - "async " for async container or empty string
* args - "getter(arg1), getter(arg2)..." or async version
* kwargs - "arg1=getter(arg1), arg2=getter(arg2)..." or async version
* cache - expression to save cache
"""
import linecache
import textwrap
from typing import cast, Any

from dishka.entities.factory_type import FactoryType
from dishka.entities.marker import Marker
from dishka.entities.key import DependencyKey
from .container_objects import CompiledFactory, Exit
from .dependency_source import Factory
from .exceptions import NoContextValueError, UnsupportedFactoryError


def make_args(args: list[str], kwargs: dict[str, str]) -> str:
    """Format arguments for the factory function."""
    return ", ".join(
        [f"{{await}}getter({arg})" for arg in args] +
        [f"{arg}={{await}}getter({var})" for arg, var in kwargs.items()],
    )


GENERATOR = """\
generator = source({args})
solved = next(generator)
exits.append(Exit(factory_type, generator))
"""
ASYNC_GENERATOR = """\
generator = source({args})
solved = await anext(generator)
exits.append(Exit(factory_type, generator))
"""
FACTORY = """\
solved = source({args})
"""
ASYNC_FACTORY = """\
solved = await source({args})
"""
VALUE = """\
solved=source
"""
ALIAS = """\
solved = {args}
"""
CONTEXT = """\
try:
    solved = context[provides.type_hint]
except KeyError:
    raise NoContextValueError(provides.type_hint)
else:
    {cache}
    return solved
"""
INVALID = """\
raise UnsupportedFactoryError(
    f"Unsupported factory type {{factory_type}}.",
)
"""
SELECTOR = """"""


ASYNC_BODIES = {
    FactoryType.ASYNC_FACTORY: ASYNC_FACTORY,
    FactoryType.FACTORY: FACTORY,
    FactoryType.ASYNC_GENERATOR: ASYNC_GENERATOR,
    FactoryType.GENERATOR: GENERATOR,
    FactoryType.VALUE: VALUE,
    FactoryType.CONTEXT: CONTEXT,
    FactoryType.ALIAS: ALIAS,
    FactoryType.SELECTOR: SELECTOR,
}
SYNC_BODIES = {
    FactoryType.FACTORY: FACTORY,
    FactoryType.GENERATOR: GENERATOR,
    FactoryType.VALUE: VALUE,
    FactoryType.CONTEXT: CONTEXT,
    FactoryType.ALIAS: ALIAS,
    FactoryType.SELECTOR: SELECTOR,
}

CACHE = """\
context[provides] = solved
"""

FUNC = """
{async}def get(getter, exits, cache, context):
{body}
{when_body}
{cache}
    return solved
"""

def _render_when_depends(
    await_: str,
    global_objects: dict[Any, str],
    when_depends: dict[DependencyKey, Marker],
) -> str:
    res = ""
    for key, marker in when_depends.items():
        if not res:
            keyword = "if"
        else:
            keyword = "elif"
        # TODO expand markers
        key_name = global_objects[key]
        marker_name = global_objects[marker]
        res += f"{keyword} {await_}getter({marker_name}):\n"
        res += f"    solved = {await_} source({key_name})\n"

    return res


def compile_factory(*, factory: Factory, is_async: bool) -> CompiledFactory:
    args = {
        f"_dishka_arg{i}": dep
        for i, dep in enumerate(factory.dependencies)
    }
    kwargs_to_globals = {
        name: f"_dishka_kwarg_{name}"
        for name in factory.kw_dependencies
    }
    kwargs = {
        kwargs_to_globals[name]: dep
        for name, dep in factory.kw_dependencies.items()
    }
    marked_deps = {
        f"_dishka_when{i}": dep
        for i, dep in enumerate(factory.when_dependencies)
    }
    marked_globals: dict[Any, str] = {
        marked_deps[name]: name
        for name in marked_deps
    }
    markers = {
        f"_dishka_marker{i}": marker
        for i, marker in enumerate(factory.when_dependencies.values())
    }
    for name, marker in markers.items():
        marked_globals[marker] = name

    if is_async:
        async_ = "async "
        await_ = "await "
        body_template = ASYNC_BODIES.get(factory.type, INVALID)
    else:
        async_ = ""
        await_ = ""
        body_template = SYNC_BODIES.get(factory.type, INVALID)

    args_str = make_args(list(args), kwargs_to_globals).format_map({
        "async": async_,
        "await": await_,
    })
    body_str = body_template.format(args=args_str)
    when_body_str = _render_when_depends(
        await_,
        marked_globals,
        factory.when_dependencies,
    )
    cache_str = CACHE if factory.cache else ""
    function_str = FUNC.format_map({
        "async": async_,
        "await": await_,
        "body": textwrap.indent(body_str, "    "),
        "when_body": textwrap.indent(when_body_str, "    "),
        "cache": textwrap.indent(cache_str, "    "),
    })

    func_globals = {
        "source": factory.source,
        "provides": factory.provides,
        "factory_type": factory.type,
        "Exit": Exit,
        "NoContextValueError": NoContextValueError,
        "UnsupportedFactoryError": UnsupportedFactoryError,
        **args,
        **kwargs,
        **marked_deps,
        **markers,
    }

    source_file_name = f"__dishka_factory_{id(factory)}"
    if is_async:
        source_file_name += "_async"
    lines = function_str.splitlines(keepends=True)
    linecache.cache[source_file_name] = (
        len(function_str), None, lines, source_file_name,
    )
    compiled = compile(function_str, source_file_name, "exec")
    exec(compiled, func_globals)  # noqa: S102
    # typing.cast is called because func_globals["get"] is not typed
    return cast(CompiledFactory, func_globals["get"])
