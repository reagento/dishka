from collections.abc import Iterator, MutableMapping
from typing import Any, NoReturn

from .entities.key import DependencyKey


class ContextProxy(MutableMapping[DependencyKey, Any]):
    def __init__(
            self,
            context: dict[Any, Any] | None,
            cache: dict[DependencyKey, Any],
    ) -> None:
        self._cache = cache
        self._context = context

    def __setitem__(self, key: DependencyKey, value: Any) -> None:
        self._cache[key] = value
        if self._context is None:
            self._context = {}
        self._context[key.type_hint] = value

    def __delitem__(self, key: DependencyKey) -> NoReturn:
        raise RuntimeError(  # noqa: TRY003
            "Cannot delete anything from context",
        )

    def __getitem__(self, key: DependencyKey) -> Any:
        if key in self._cache:
            return self._cache[key]
        if self._context is None:
            raise KeyError(key)
        return self._context[key.type_hint]

    def __len__(self) -> int:
        return len(self._cache)

    def __iter__(self) -> Iterator[DependencyKey]:
        return iter(self._cache)
