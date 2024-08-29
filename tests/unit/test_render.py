import textwrap

import pytest

from dishka.dependency_source.make_factory import make_factory
from dishka.error_rendering import PathRenderer


class A:
    def foo(self) -> int:
        pass


@pytest.fixture
def renderer():
    return PathRenderer()


def test_cycle(renderer):
    foo = A().foo
    factory = make_factory(
        provides=None,
        source=foo,
        cache=False,
        scope=None,
        is_in_class=True,
        override=False,
    )

    res = renderer.render([factory, factory, factory])
    res = textwrap.dedent(res)
    assert res == textwrap.dedent("""\
              ~~~ component=None, None ~~~
         → →  <class 'int'> A.foo
        ↑   ↓ <class 'int'> A.foo
         ← ←  <class 'int'> A.foo
    """)


def test_cycle_1(renderer):
    foo = A().foo
    factory = make_factory(
        provides=None,
        source=foo,
        cache=False,
        scope=None,
        is_in_class=True,
        override=False,
    )

    res = renderer.render([factory])
    res = textwrap.dedent(res)
    assert res == textwrap.dedent("""\
      ~~~ component=None, None ~~~
    ⥁ <class 'int'> A.foo
    """)


def test_linear(renderer):
    foo = A().foo
    factory = make_factory(
        provides=None,
        source=foo,
        cache=False,
        scope=None,
        is_in_class=True,
        override=False,
    )

    res = renderer.render([factory, factory], last=factory.provides)
    res = textwrap.dedent(res)
    assert res == textwrap.dedent("""\
       ~~~ component=None, None ~~~
    ↓  <class 'int'> A.foo
    ↓  <class 'int'> A.foo
     → <class 'int'> ???
    """)
