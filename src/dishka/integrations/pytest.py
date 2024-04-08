from inspect import signature
from typing import Any

import pytest

from dishka import Container
from .base import default_parse_dependency, get_type_hints


@pytest.fixture(autouse=True)
def _dishka_inject(
        request: pytest.FixtureRequest,
):
    dependencies = {}
    parse_dependency = default_parse_dependency
    hints = get_type_hints(request.function, include_extras=True)
    func_signature = signature(request.function)
    for name, param in func_signature.parameters.items():
        hint = hints.get(name, Any)
        dep = parse_dependency(param, hint)
        if dep is None:
            continue
        dependencies[name] = dep

    if dependencies:
        container: Container = request.getfixturevalue("dishka_container")
        for name, dep in dependencies.items():
            request.node.funcargs[name] = container.get(
                dep.type_hint, component=dep.component,
            )
