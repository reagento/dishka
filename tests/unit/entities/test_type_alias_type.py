import sys

import pytest

from dishka.entities.type_alias_type import unwrap_type_alias

if sys.version_info < (3, 12):
    pytest.skip(
        "PEP 695 type aliases require Python 3.12+",
        allow_module_level=True,
    )

from typing import TypeAliasType

from .cyclic_aliases import MutualA, MutualB, SelfCycle


def test_unwrap_returns_non_alias_unchanged():
    assert unwrap_type_alias(int) is int


def test_unwrap_single_alias():
    assert unwrap_type_alias(TypeAliasType("IntAlias", int)) is int


def test_unwrap_nested_alias():
    inner = TypeAliasType("Inner", str)
    outer = TypeAliasType("Outer", inner)
    assert unwrap_type_alias(outer) is str


def test_unwrap_self_referential_alias_terminates():
    # Would spin forever without the cycle guard.
    assert unwrap_type_alias(SelfCycle) is SelfCycle


def test_unwrap_mutually_referential_aliases_terminate():
    assert unwrap_type_alias(MutualA) in (MutualA, MutualB)
