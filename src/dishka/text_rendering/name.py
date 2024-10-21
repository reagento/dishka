from typing import Any, get_args, get_origin


def _render_args(hint: Any) -> str:
    args = get_args(hint)
    return ", ".join(
        get_name(arg, include_module=False)
        for arg in args
    )


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
    if name:
        if get_origin(hint):
            args = f"[{_render_args(hint)}]"
        else:
            args = ""
        return f"{module}{name}{args}"
    return str(hint)
