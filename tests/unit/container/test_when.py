import pytest

from dishka import Has, Provider, Scope, make_container


@pytest.mark.parametrize(
    ("provides", "value"), [
        (int, "int"),
        (float, "float"),
        (complex, "default"),
    ],
)
def test_provider_has_cls(provides, value):
    p = Provider()
    p.provide(lambda: 42, provides=provides, scope=Scope.APP)
    p.provide(lambda: "default", provides=str, scope=Scope.APP)
    p.provide(lambda: "int", provides=str, scope=Scope.APP, when=Has(int))
    p.provide(lambda: "float", provides=str, scope=Scope.APP, when=Has(float))
    c = make_container(p)

    assert c.get(str) == value
