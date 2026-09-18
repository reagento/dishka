from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

from dishka import DishkaModule, FromDishka

module = DishkaModule()


class Dependency:
    pass


@module.inject
def generate(dependency: FromDishka[Dependency]) -> Iterator[Dependency]:
    yield dependency


@module.inject
async def generate_async(
    dependency: FromDishka[Dependency],
) -> AsyncIterator[Dependency]:
    yield dependency
