import pytest

import dishka
from dishka.text_rendering import get_name


class A0:
    class A1:
        def foo(self): ...

        @staticmethod
        def foo_class(param): ...

    def bar(self): ...


def baz(): ...


@pytest.mark.parametrize(
    ("obj", "include_module", "name"), [
        (A0, False, "A0"),
        (A0, True, "unit.text_rendering.test_name.A0"),
        (A0.A1, False, "A0.A1"),
        (A0.A1.foo, False, "A0.A1.foo"),
        (A0.A1.foo_class, False, "A0.A1.foo_class"),
        (A0.bar, False, "A0.bar"),
        (baz, False, "baz"),
        (int, False, "int"),
        (str, True, "str"),
        (None, False, "None"),
        (..., False, "..."),
        (dishka.Scope, True, "dishka.entities.scope.Scope"),
    ],
)
def test_get_name(obj, include_module, name):
    assert get_name(obj, include_module=include_module) == name
