import collections.abc
import types
import typing
from typing import Any, ParamSpec, Union

from ..feature_requirement import HAS_TYPE_ALIAS_SYNTAX, HAS_UNPACK
from .fundamentals import get_generic_args, strip_alias

NoneType = type(None)


class TypeHintRenderer:
    __slots__ = ("_uri_faced", )

    def __init__(self, *, uri_faced: bool):
        self._uri_faced = uri_faced

    def _join_render(self, sep: str, objs: collections.abc.Iterable[Any]) -> str:
        return sep.join(self.render_type(obj) for obj in objs)

    def _render_union(self, tp, origin, args) -> str:
        if len(args) == 2:  # noqa: PLR2004
            if args[0] is NoneType:
                args = [args[1]]
            elif args[1] is NoneType:
                args = [args[0]]

        return self._render_parametrized_generic(tp, origin, args)

    def _render_union_op(self, tp, origin, args) -> str:
        if self._uri_faced:
            return self._join_render("_or_", args)
        return self._join_render(" | ", args)

    def _render_unpack(self, tp, origin, args) -> str:
        if self._uri_faced:
            return self.render_type(args[0])
        return f"*{self.render_type(args[0])}"

    def _get_repr_base(self, tp, origin) -> str:
        if HAS_TYPE_ALIAS_SYNTAX and isinstance(origin, typing.TypeAliasType):  # type: ignore[attr-defined]
            return tp.__name__
        return tp.__qualname__

    def _render_callable(self, tp, origin, args) -> str:
        if isinstance(args[0], ParamSpec):
            return self._render_parametrized_generic(tp, origin, args)
        base = self._get_repr_base(tp, origin)
        if args[0] == Ellipsis:
            if self._uri_faced:
                return f"{base}_..._{self.render_type(args[1])}"
            return f"{base}[..., {self.render_type(args[1])}]"
        if self._uri_faced:
            return f"{base}_{self._join_render('_', [*args[0], args[1]])}"
        return f"{base}[[{self._join_render(', ', args[0])}], {self.render_type(args[1])}]"

    def _render_parametrized_generic(self, tp, origin, args) -> str:
        base = self._get_repr_base(tp, origin)
        if self._uri_faced:
            return f"{base}_{self._join_render('_', args)}"
        return f"{base}[{self._join_render(', ', args)}]"

    def render_type(self, obj) -> str:  # noqa: PLR0911
        origin = strip_alias(obj)
        args = get_generic_args(obj)

        if obj is NoneType:
            return "None"
        if type(obj) is types.UnionType:
            return self._render_union_op(obj, origin, args)
        if origin == Union:  # this branch is inactive at PY_314
            return self._render_union(obj, origin, args)
        if isinstance(obj, ParamSpec):
            return obj.__name__
        if HAS_UNPACK and origin == typing.Unpack:
            return self._render_unpack(obj, origin, args)
        if args:
            if origin == collections.abc.Callable:
                return self._render_callable(obj, origin, args)
            return self._render_parametrized_generic(obj, origin, args)
        if isinstance(obj, type):
            return obj.__qualname__
        return self._get_repr_without_module(obj, origin)

    def _get_repr_without_module(self, obj, origin) -> str:
        module = getattr(obj, "__module__", None)
        try:
            obj_repr = repr(obj)
        except Exception as ex:
            obj_repr = f"<repr failed: {type(ex)}>"
        if module is not None and obj_repr.startswith(module + "."):
            return obj_repr[len(module) + 1:]
        return obj_repr
