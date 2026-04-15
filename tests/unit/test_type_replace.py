from collections.abc import Callable
from typing import Annotated, Generic, Optional, TypeVar, Union

import pytest

from dishka.dependency_source.type_replace import replace_type


class Self:
    pass


class Dummy:
    pass


T = TypeVar("T")


class MyGeneric(Generic[T]):
    pass


@pytest.mark.parametrize(
    ("hint", "expected"),
    [
        (Self, Dummy),
        (list[Self], list[Dummy]),
        (list[list[Self]], list[list[Dummy]]),
        (dict[str, Self], dict[str, Dummy]),
        (tuple[int, Self], tuple[int, Dummy]),
        (tuple[Self, ...], tuple[Dummy, ...]),
        (type[Self], type[Dummy]),
        (Self | None, Dummy | None),
        (Union[Self, None], Union[Dummy, None]),
        (Optional[Self], Optional[Dummy]),
        (MyGeneric[Self], MyGeneric[Dummy]),
        (MyGeneric[int], MyGeneric[int]),
        (list[Self | int], list[Dummy | int]),
        (Annotated[Self, "meta", Self], Annotated[Dummy, "meta", Self]),
        (Callable[..., Self], Callable[..., Dummy]),
        (Callable[[Self, int], Self], Callable[[Dummy, int], Dummy]),
    ],
)
def test_replace_type_parametrized(hint, expected):
    assert replace_type(hint, Self, Dummy) == expected
