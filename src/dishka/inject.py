from inspect import Parameter, signature, Signature
from typing import (
    Any, Annotated, Callable, Sequence, get_type_hints, get_origin, get_args,
)

from .container import Container


class Depends:
    def __init__(self, param: Any = None):
        self.param = param


def wrap_injection(
        func: Callable,
        container_getter: Callable[[dict], Container],
        remove_depends: bool = True,
        additional_params: Sequence[Parameter] = (),
        is_async: bool = False,
):
    hints = get_type_hints(func, include_extras=True)
    func_signature = signature(func)

    dependencies = {}
    for name, hint in hints.items():
        if get_origin(hint) is not Annotated:
            continue
        dep = next(
            (arg for arg in get_args(hint) if isinstance(arg, Depends)),
            None,
        )
        if not dep:
            continue
        if dep.param is None:
            dependencies[name] = get_args(hint)[0]
        else:
            dependencies[name] = dep.param

    if remove_depends:
        new_annotations = {
            name: hint
            for name, hint in hints.items()
            if name not in dependencies
        }
        new_params = [
            param
            for name, param in func_signature.parameters.items()
            if name not in dependencies
        ]
    else:
        new_annotations = hints.copy()
        new_params = func_signature.parameters.copy()

    if additional_params:
        new_params.extend(additional_params)
        for param in additional_params:
            new_annotations[param.name] = param.annotation

    if is_async:
        async def autoinjected_func(**kwargs):
            container = container_getter(kwargs)
            for param in additional_params:
                kwargs.pop(param.name)
            solved = {
                name: await container.get(dep)
                for name, dep in dependencies.items()
            }
            return await func(**kwargs, **solved)
    else:
        def autoinjected_func(**kwargs):
            container = container_getter(kwargs)
            for param in additional_params:
                kwargs.pop(param.name)
            solved = {
                name: container.get(dep)
                for name, dep in dependencies.items()
            }
            return func(**kwargs, **solved)

    autoinjected_func.__name__ = func.__name__
    autoinjected_func.__doc__ = func.__doc__
    autoinjected_func.__annotations__ = new_annotations
    autoinjected_func.__signature__ = Signature(
        parameters=new_params,
        return_annotation=func_signature.return_annotation,
    )
    return autoinjected_func
