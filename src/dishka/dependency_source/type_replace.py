import collections.abc
import types
import typing
from typing import Any


def _replace_type(type_hint: Any, old: Any, new: Any) -> Any:  # noqa: PLR0911
    if type_hint == old:
        return new
    if (
        (origin := typing.get_origin(type_hint)) is None
        or not (args := typing.get_args(type_hint))
    ):
        return type_hint

    if origin is typing.Annotated:
        base, *meta = args
        args = _replace_type(base, old, new), *meta
        return typing.Annotated[args]

    if origin in (typing.Union, types.UnionType):
        new_args = tuple(_replace_type(arg, old, new) for arg in args)
        out = new_args[0]
        for arg in new_args[1:]:
            out = out | arg
        return out

    if origin in (typing.Callable, collections.abc.Callable):
        params, ret = args
        new_ret = _replace_type(ret, old, new)

        if params is Ellipsis:
            return origin[..., new_ret]
        new_params = [_replace_type(p, old, new) for p in params]
        return origin[new_params, new_ret]

    new_args = tuple(_replace_type(arg, old, new) for arg in args)
    return origin[new_args]


def replace_type(type_hint: Any, old: Any, new: Any) -> Any:
    try:
        return _replace_type(type_hint, old, new)
    except Exception:  # noqa: BLE001
        return type_hint
