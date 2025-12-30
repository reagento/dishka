import linecache
import re
import textwrap
from typing import Any, cast

from dishka.container_objects import CompiledFactory, Exit
from dishka.dependency_source import Factory
from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.marker import AndMarker, BaseMarker, NotMarker, OrMarker
from dishka.exceptions import NoContextValueError, UnsupportedFactoryError
from dishka.text_rendering import get_name

IDENTIFIER = re.compile("[a-zA-Z_][a-zA-Z_0-9]*]")
NOT_ALLOWED_SYMBOLS = re.compile("[^a-zA-Z0-9_]")

GENERATOR = """\
generator = {source}({args})
{result_name} = next(generator)
exits.append(Exit(factory_type, generator))
"""
ASYNC_GENERATOR = """\
generator = {source}({args})
{result_name} = await anext(generator)
exits.append(Exit(factory_type, generator))
"""
FACTORY = """\
{result_name} = {source}({args})
"""
ASYNC_FACTORY = """\
{result_name} = await {source}({args})
"""
VALUE = """\
{result_name} = {source}
"""
ALIAS = """\
{result_name} = {args}
"""
CONTEXT = """\
{result_name} = context[provides]
"""
INVALID = """\
raise UnsupportedFactoryError(
    f"Unsupported factory type {{factory_type}}.",
)
"""

ASYNC_BODIES = {
    FactoryType.ASYNC_FACTORY: ASYNC_FACTORY,
    FactoryType.FACTORY: FACTORY,
    FactoryType.ASYNC_GENERATOR: ASYNC_GENERATOR,
    FactoryType.GENERATOR: GENERATOR,
    FactoryType.VALUE: VALUE,
    FactoryType.CONTEXT: CONTEXT,
    FactoryType.ALIAS: ALIAS,
}
SYNC_BODIES = {
    FactoryType.FACTORY: FACTORY,
    FactoryType.GENERATOR: GENERATOR,
    FactoryType.VALUE: VALUE,
    FactoryType.CONTEXT: CONTEXT,
    FactoryType.ALIAS: ALIAS,
}

CACHE = """\
context[provides] = solved
"""

FUNC = """
{async}def {function_name}(getter, exits, context):
{body}
{cache}
    return {result_name}
"""


class FactoryCompiler:
    def __init__(self, *, async_container: bool):
        self.key_vars: dict[DependencyKey, str] = {}
        self.used_names = set()
        if async_container:
            self.await_ = "await "
            self.async_ = "async "
            self.body_templates = ASYNC_BODIES
        else:
            self.await_ = ""
            self.async_ = ""
            self.body_templates = SYNC_BODIES

    def key_name(self, key: Any) -> str:
        if key in self.key_vars:
            return self.key_vars[key]

        if isinstance(key, DependencyKey):
            name = get_name(key.type_hint, include_module=False)
        else:
            name = get_name(key, include_module=False)
        name = NOT_ALLOWED_SYMBOLS.sub("_", name)
        if name[0] in "0123456789":
            name = "_" + name

        base_name = name
        count = 0
        while name in self.used_names:
            name = f"{base_name}{count}"
        self.used_names.add(name)
        self.key_vars[key] = name
        return name

    def get_from_container(self, key: DependencyKey, provides: DependencyKey):
        if key == provides:
            return "solved"
        name = self.key_name(key)
        return f"{self.await_}getter({name})"

    def call_args_expr(
            self,
            args: list[DependencyKey],
            kwargs: dict[str, DependencyKey],
            provides: DependencyKey,
    ):
        return ", ".join(
            [self.get_from_container(key, provides) for key in args] +
            [f"{name}=" + self.get_from_container(key, provides) for name, key in
             kwargs.items()],
        )

    def when(self, marker: BaseMarker | None):
        if not marker:
            return ""
        if isinstance(marker, AndMarker):
            left = self.when(marker.left)
            right = self.when(marker.right)
            return f"({left}) and ({right})"
        if isinstance(marker, OrMarker):
            left = self.when(marker.left)
            right = self.when(marker.right)
            return f"({left}) or ({right})"
        if isinstance(marker, NotMarker):
            nested = self.when(marker.marker)
            return f"not ({nested})"
        key = DependencyKey(marker, component=DEFAULT_COMPONENT)
        return self.get_from_container(key, None)

    def call_factory(self, factory: Factory):
        args_str = self.call_args_expr(factory.dependencies,
                                       factory.kw_dependencies,
                                       factory.provides)
        body_str = self.body_templates[factory.type].format(
            args=args_str,
            result_name="solved",
            source=self.key_name(factory.source),
        )
        return body_str

    def render_decorated_factory(self, factory: Factory):
        body = self.call_factory(factory)
        for decorator in factory.connected_factories:
            when = self.when(decorator.when)
            nested_body = self.render_decorated_factory(decorator)
            if when:
                body += f"if {when}:\n"
                body += textwrap.indent(nested_body, " " * 4)
            else:
                body += nested_body
        return body

    def render_selector_factory(self, factory: Factory):
        body = self.call_factory(factory)
        for n, decorator in enumerate(factory.connected_factories):
            when = self.when(decorator.when)
            nested_body = self.render_decorated_factory(decorator)
            if when:
                if n==0:
                    body += f"if {when}:\n"
                else:
                    body += f"elif {when}:\n"
                body += textwrap.indent(nested_body, " " * 4)
            else:
                body += nested_body
                # TODO raise error?
                break
        return body

    def compile(self, factory: Factory) -> CompiledFactory:
        func_globals = {
            "source": factory.source,
            "provides": factory.provides,
            "factory_type": factory.type,
            "Exit": Exit,
            "NoContextValueError": NoContextValueError,
            "UnsupportedFactoryError": UnsupportedFactoryError,
        }
        self.used_names.update(func_globals)
        function_name = f"get_{self.key_name(factory.provides)}"
        self.used_names.add(function_name)

        cache_str = CACHE if factory.cache else ""

        if factory.type is FactoryType.SELECTOR:
            body_str = self.render_selector_factory(factory)
        else:
            body_str = self.render_decorated_factory(factory)

        function_str = FUNC.format_map({
            "async": self.async_,
            "await": self.await_,
            "body": textwrap.indent(body_str, " "*4),
            "cache": textwrap.indent(cache_str, " "*4),
            "function_name": function_name,
            "result_name": "solved",
        })

        for key, name in self.key_vars.items():
            func_globals[name] = key

        source_file_name = f"<__dishka_factory_{self.key_name(factory.provides)}{self.async_}>"
        lines = function_str.splitlines(keepends=True)
        linecache.cache[source_file_name] = (
            len(function_str), None, lines, source_file_name,
        )
        compiled = compile(function_str, source_file_name, "exec")
        exec(compiled, func_globals)  # noqa: S102
        # typing.cast is called because func_globals["function_name"] is not typed
        return cast(CompiledFactory, func_globals[function_name])
