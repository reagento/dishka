"""Dishka benchmark helpers: minimal scopes, no lock factory, and validation skipped."""

from __future__ import annotations

from typing import Any

from dishka import BaseScope, Container, Provider, make_container, new_scope


class DishkaBenchmarkScope(BaseScope):
    APP = new_scope("APP")
    REQUEST = new_scope("REQUEST")


def make_dishka_benchmark_container(
    *providers: Provider,
    context: dict[Any, Any] | None = None,
) -> Container:
    return make_container(
        *providers,
        scopes=DishkaBenchmarkScope,
        lock_factory=None,
        skip_validation=True,
        context=context,
    )
