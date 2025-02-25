from dishka._adaptix.common import TypeHint
from dishka.exception_base import DishkaError


class StartingClassIgnoredError(ValueError, DishkaError):
    def __init__(self, hint: TypeHint) -> None:
        self.hint = hint

    def __str__(self) -> str:
        return f"The starting class {self.hint!r} is in ignored types"
