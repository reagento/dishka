from enum import Enum
from typing import TypeAlias, TypeVar


class Special(Enum):
    OMITTED = "omitted"


T = TypeVar("T")
MayBe: TypeAlias = Special | T


def coalesce(a: MayBe[T], b: T) -> T:
    if a is Special.OMITTED:
        return b
    return a
