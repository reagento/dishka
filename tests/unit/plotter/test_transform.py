from typing import Protocol

from dishka import Provider, Scope, make_container
from dishka.plotter.model import Group, GroupType, Node, NodeType
from dishka.plotter.transform import Transformer


def test_empty():
    container = make_container()
    res = Transformer().transform(container)
    assert not res


class A:
    pass


class B:
    def __init__(self, a: A):
        pass


class P(Protocol):
    pass


EXPECTED_GRAPH = [
    Group(
        id="scope1",
        name="Scope.APP",
        children=[
            Group(
                id="component2",
                name="",
                children=[],
                nodes=[
                    Node(
                        id="factory3",
                        name="Container",
                        dependencies=[],
                        type=NodeType.CONTEXT,
                        is_protocol=False,
                        source_name="",
                    ),
                    Node(
                        id="factory4",
                        name="A",
                        dependencies=[],
                        type=NodeType.FACTORY,
                        is_protocol=False,
                        source_name="A",
                    ),
                    Node(
                        id="factory5",
                        name="B",
                        dependencies=["factory4"],
                        type=NodeType.FACTORY,
                        is_protocol=False,
                        source_name="B",
                    ),
                    Node(
                        id="factory6",
                        name="P",
                        dependencies=["factory9"],
                        type=NodeType.DECORATOR,
                        is_protocol=True,
                        source_name="p_decorator",
                    ),
                    Node(
                        id="factory7",
                        name="float",
                        dependencies=["factory6"],
                        type=NodeType.ALIAS,
                        is_protocol=False,
                        source_name="",
                    ),
                    Node(
                        id="factory9",
                        name="P",
                        dependencies=[],
                        type=NodeType.FACTORY,
                        is_protocol=True,
                        source_name="test_deps.<locals>.<lambda>",
                    ),
                ],
                type=GroupType.COMPONENT,
            ),
        ],
        nodes=[],
        type=GroupType.SCOPE,
    ),
]


def p_decorator(p: P) -> P:
    return p


def test_deps():
    provider = Provider(scope=Scope.APP)
    provider.provide(A)
    provider.provide(B)
    provider.provide(lambda: 0, provides=P)
    provider.decorate(p_decorator)
    provider.alias(source=P, provides=float)
    container = make_container(provider)
    res = Transformer().transform(container)
    assert res == EXPECTED_GRAPH


def cycle1(x: int) -> float:
    pass


def cycle2(x: float) -> int:
    pass


EXPECTED_CYCLE_GRAPH = [
    Group(
        id="scope1",
        name="Scope.APP",
        children=[
            Group(
                id="component2",
                name="",
                children=[],
                nodes=[
                    Node(
                        id="factory3",
                        name="Container",
                        dependencies=[],
                        type=NodeType.CONTEXT,
                        is_protocol=False,
                        source_name="",
                    ),
                    Node(
                        id="factory4",
                        name="B",
                        dependencies=[],
                        type=NodeType.FACTORY,
                        is_protocol=False,
                        source_name="B",
                    ),
                    Node(
                        id="factory5",
                        name="float",
                        dependencies=["factory6"],
                        type=NodeType.FACTORY,
                        is_protocol=False,
                        source_name="cycle1",
                    ),
                    Node(
                        id="factory6",
                        name="int",
                        dependencies=["factory5"],
                        type=NodeType.FACTORY,
                        is_protocol=False,
                        source_name="cycle2",
                    ),
                ],
                type=GroupType.COMPONENT,
            ),
        ],
        nodes=[],
        type=GroupType.SCOPE,
    ),
]


def test_invalid():
    provider = Provider(scope=Scope.APP)
    provider.provide(B)
    provider.provide(cycle1)
    provider.provide(cycle2)
    container = make_container(provider, skip_validation=True)
    res = Transformer().transform(container)
    assert res == EXPECTED_CYCLE_GRAPH


COMPONENT = "comp1"

COMPONENT_GRAPH = [
    Group(
        id="scope1",
        name="Scope.APP",
        children=[
            Group(
                id="component2",
                name="",
                children=[],
                nodes=[
                    Node(
                        id="factory3",
                        name="Container",
                        dependencies=[],
                        type=NodeType.CONTEXT,
                        is_protocol=False,
                        source_name="",
                    ),
                    Node(
                        id="factory7",
                        name="B",
                        dependencies=[
                            "factory8",
                        ],
                        type=NodeType.FACTORY,
                        is_protocol=False,
                        source_name="B",
                    ),
                    Node(
                        id="factory8",
                        name="A",
                        dependencies=[
                            "factory6",
                        ],
                        type=NodeType.ALIAS,
                        is_protocol=False,
                        source_name="",
                    ),
                ],
                type=GroupType.COMPONENT,
            ),
            Group(
                id="component4",
                name="comp1",
                children=[],
                nodes=[
                    Node(
                        id="factory5",
                        name="Container",
                        dependencies=["factory3"],
                        type=NodeType.ALIAS,
                        is_protocol=False,
                        source_name="",
                    ),
                    Node(
                        id="factory6",
                        name="A",
                        dependencies=[],
                        type=NodeType.FACTORY,
                        is_protocol=False,
                        source_name="A",
                    ),
                ],
                type=GroupType.COMPONENT,
            ),
        ],
        nodes=[],
        type=GroupType.SCOPE,
    ),
]


def test_components():
    component_provider = Provider(scope=Scope.APP, component=COMPONENT)
    component_provider.provide(source=A)
    provider = Provider(scope=Scope.APP)
    provider.alias(source=A, component=COMPONENT)
    provider.provide(B)
    container = make_container(component_provider, provider)
    res = Transformer().transform(container)
    assert res == COMPONENT_GRAPH
