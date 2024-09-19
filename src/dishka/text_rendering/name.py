from typing import Any


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
        return f"{module}{name}"
    return str(hint)
