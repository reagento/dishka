"""
globals expected:
* source
* Exit
* factory_type
* provides

format params:
* await
* async
* args
* cache
"""
from collections.abc import Callable
from dataclasses import dataclass

from .dependency_source import Factory, FactoryType
from .exceptions import NoContextValueError, UnsupportedFactoryError


def make_args(names: list[str]):
    return ", ".join(
        "{await} getter(%s)" % arg
        for arg in names
    )


GENERATOR = """
{async}def get(getter, exits, context):
    generator = source({args})
    solved = next(generator)
    exits.append(Exit(factory_type, generator))
    {cache}
    return solved
"""
ASYNC_GENERATOR = """
{async}def get(getter, exits, context):
    generator = source({args})
    solved = await anext(generator)
    exits.append(Exit(factory_type, generator))
    {cache}
    return solved
"""
FACTORY = """
{async}def get(getter, exits, context):
    solved = source({args})
    {cache}
    return solved
"""
ASYNC_FACTORY = """
{async}def get(getter, exits, context):
    solved = await source({args})
    {cache}
    return solved
"""
VALUE = """
{async}def get(getter, exits, context):
    return source
"""
ALIAS = """
{async}def get(getter, exits, context):
    return {args}
"""
CONTEXT = """
{async}def get(getter, exits, context):
    raise NoContextValueError()
"""
INVALID = """
{async}def get(getter, exits, context):
    raise UnsupportedFactoryError(
        f"Unsupported factory type {factory_type}.",
    )
"""

BODIES = {
    FactoryType.ASYNC_FACTORY: ASYNC_FACTORY,
    FactoryType.FACTORY: FACTORY,
    FactoryType.ASYNC_GENERATOR: ASYNC_GENERATOR,
    FactoryType.GENERATOR: GENERATOR,
    FactoryType.VALUE: VALUE,
    FactoryType.CONTEXT: CONTEXT,
    FactoryType.ALIAS: ALIAS,
}

CACHE = "context[provides] = solved"


@dataclass
class Exit:
    __slots__ = ("type", "callable")
    type: FactoryType
    callable: Callable


def compile_factory(*, factory: Factory, is_async: bool) -> Callable:
    names = {f"arg{i}": dep for i, dep in enumerate(factory.dependencies)}
    if is_async:
        async_ = "async "
        await_ = "await"
    else:
        async_ = ""
        await_ = ""
    if factory.cache:
        cache = CACHE
    else:
        cache = ""
    body_template = BODIES.get(factory.type, INVALID)

    args = make_args(list(names)).format_map({"await": await_})
    body = body_template.format_map({
        "async": async_,
        "await": await_,
        "args": args,
        "cache": cache,
    })
    func_globals = {
        "source": factory.source,
        "provides": factory.provides,
        "Exit": Exit,
        "factory_type": factory.type,
        "NoContextValueError": NoContextValueError,
        "UnsupportedFactoryError": UnsupportedFactoryError,
        **names,
    }
    exec(body, func_globals)
    return func_globals["get"]
