from typing import Any, get_args

from dishka._adaptix.type_tools import is_generic, strip_alias


def get_name(hint: Any, *, include_module: bool) -> str:
    if hint is ...:
        return "..."
    if func := getattr(object, "__func__", None):
        return get_name(func, include_module=include_module)

    if include_module:
        module = getattr(hint, "__module__", "")
        if module == "builtins":
            module = ""
        elif module:
            module += "."
    else:
        module = ""

    name = (
        getattr(hint, "__qualname__", None) or
        getattr(hint, "__name__", None)
    )
    if is_generic(strip_alias(hint)):
        str_args = ",".join(
            (get_name(args, include_module=False) for args in get_args(hint)),
        )
        generic_args = f"[{str_args}]"
    else:
        generic_args = ""
    if name:
        return f"{module}{name}" + generic_args
    return str(hint) + generic_args
