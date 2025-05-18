import textwrap
from typing import Annotated

import pytest

from dishka import FromComponent, Scope
from dishka.provider.make_factory import make_factory
from dishka.text_rendering.path import PathRenderer


class A:
    def foo(self) -> int:
        pass


@pytest.fixture
def cycle_renderer():
    return PathRenderer(cycle=True)


@pytest.fixture
def linear_renderer():
    return PathRenderer(cycle=False)


def test_cycle(cycle_renderer):
    foo = A().foo
    factory = make_factory(
        provides=None,
        source=foo,
        cache=False,
        scope=None,
        is_in_class=True,
        override=False,
    )

    res = cycle_renderer.render([factory, factory, factory])
    res = textwrap.dedent(res)
    assert res == textwrap.dedent("""\
            ◈ None, component=None ◈
      ╭─>─╮ int   A.foo
      │   ▼ int   A.foo
      ╰─<─╯ int   A.foo
    """)


def test_cycle_2scopes(cycle_renderer):
    foo = A().foo
    app_factory = make_factory(
        provides=Annotated[int, FromComponent("")],
        source=foo,
        cache=False,
        scope=Scope.APP,
        is_in_class=True,
        override=False,
    )
    factory = make_factory(
        provides=Annotated[int, FromComponent("")],
        source=foo,
        cache=False,
        scope=Scope.REQUEST,
        is_in_class=True,
        override=False,
    )


    res = cycle_renderer.render([app_factory, factory, factory, factory])
    res = textwrap.dedent(res)
    assert res == textwrap.dedent("""\
            ◈ Scope.APP, component='' ◈
      ╭─>─╮ int   A.foo
      │   │ ◈ Scope.REQUEST, component='' ◈
      │   ▼ int   A.foo
      │   ▼ int   A.foo
      ╰─<─╯ int   A.foo
    """)


def test_cycle_1(cycle_renderer):
    foo = A().foo
    factory = make_factory(
        provides=None,
        source=foo,
        cache=False,
        scope=None,
        is_in_class=True,
        override=False,
    )

    res = cycle_renderer.render([factory])
    res = textwrap.dedent(res)
    assert res == textwrap.dedent("""\
          ◈ None, component=None ◈
    ⥁ int   A.foo
    """)


def test_linear(linear_renderer):
    foo = A().foo
    factory = make_factory(
        provides=Annotated[int, FromComponent("")],
        source=foo,
        cache=False,
        scope=Scope.APP,
        is_in_class=True,
        override=False,
    )

    res = linear_renderer.render([factory, factory], last=factory.provides)
    res = textwrap.dedent(res)
    assert res == textwrap.dedent("""\
    │   ◈ Scope.APP, component='' ◈
    ▼   int   A.foo
    ▼   int   A.foo
    ╰─> int   ???  
    """)  # noqa: W291

def test_linear_2scopes(linear_renderer):
    foo = A().foo
    app_factory = make_factory(
        provides=Annotated[int, FromComponent("")],
        source=foo,
        cache=False,
        scope=Scope.APP,
        is_in_class=True,
        override=False,
    )
    factory = make_factory(
        provides=Annotated[int, FromComponent("")],
        source=foo,
        cache=False,
        scope=Scope.REQUEST,
        is_in_class=True,
        override=False,
    )

    res = linear_renderer.render(
        [app_factory, factory, factory],
        last=factory.provides,
    )
    res = textwrap.dedent(res)
    assert res == textwrap.dedent("""\
    │   ◈ Scope.APP, component='' ◈
    ▼   int   A.foo
    │   ◈ Scope.REQUEST, component='' ◈
    ▼   int   A.foo
    ▼   int   A.foo
    ╰─> int   ???  
    """)  # noqa: W291
