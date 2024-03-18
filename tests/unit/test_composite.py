from dishka.dependency_source.composite import ensure_composite


def test_composite():
    class A:
        @ensure_composite
        def foo(self, a, b):
            return a + b

    a = A()
    assert a.foo(1, 2) == 3
