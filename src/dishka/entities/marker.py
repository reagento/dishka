from dataclasses import dataclass
from typing import Any, ClassVar


class BaseMarker:
    """
    A marker used to conditionally activate dependencies.
    
    BaseMarkers can be combined using logical operators:
    - ~marker (NOT)
    - marker1 | marker2 (OR)  
    - marker1 & marker2 (AND)
    """
    def __invert__(self) -> Any:
        return NotMarker(self)

    def __or__(self, other: "BaseMarker") -> "BaseMarker":
        return OrMarker(self, other)

    def __and__(self, other: "BaseMarker") -> "BaseMarker":
        return AndMarker(self, other)


@dataclass(frozen=True, slots=True)
class Marker(BaseMarker):
    value: Any

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value!r})"


@dataclass(frozen=True, slots=True)
class NotMarker(BaseMarker):
    marker: BaseMarker

    def __invert__(self) -> "BaseMarker":
        # Double negation: ~~marker -> marker
        if isinstance(self.marker, NotMarker):
            return self.marker.marker
        return self.marker

    def __or__(self, other: "BaseMarker") -> "BaseMarker":
        return OrMarker(self, other)

    def __and__(self, other: "BaseMarker") -> "BaseMarker":
        return AndMarker(self, other)

    def __repr__(self) -> str:
        return f"~{self.marker!r}"


@dataclass(frozen=True, slots=True)
class BinOpMarker(BaseMarker):
    left: BaseMarker
    right: BaseMarker
    op: ClassVar[str]

    def _ordered_values(self):
        if id(self.left) < id(self.right):
            return self.left, self.right
        return self.right, self.left

    def __eq__(self, other: object) -> bool:
        if type(self) != type(other):
            return NotImplemented
        return self._ordered_values() == self._ordered_values()

    def __hash__(self) -> int:
        return hash(self._ordered_values())

    def __repr__(self) -> str:
        return f"({self.left!r} {self.op} {self.right!r})"


@dataclass(frozen=True, slots=True, repr=False)
class OrMarker(BinOpMarker):
    op: ClassVar[str] = "|"

    def __invert__(self) -> Any:
        # De Morgan's law: ~(A | B) = ~A & ~B
        return AndMarker(~self.left, ~self.right)


@dataclass(frozen=True, slots=True, repr=False)
class AndMarker(BinOpMarker):
    op: ClassVar[str] = "&"

    def __invert__(self) -> Any:
        # De Morgan's law: ~(A & B) = ~A | ~B
        return OrMarker(~self.left, ~self.right)


@dataclass(frozen=True, slots=True)
class Has(Marker):
    """Special marker for checking if a type is available in the graph.
    
    Used to check if a dependency can be created or is registered.
    """
    def __repr__(self) -> str:
        return f"Has({self.value.__name__})"
