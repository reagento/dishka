from typing import Any


class DishkaError(Exception):
    pass


class InvalidMarkerError(DishkaError):
    def __init__(self, marker: Any) -> None:
        self.marker = marker

    def __str__(self) -> str:
        return f"Cannot use {self.marker!r} as marker."
