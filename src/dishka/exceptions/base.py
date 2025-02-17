try:
    from builtins import ExceptionGroup  # type: ignore[attr-defined]

except ImportError:
    from exceptiongroup import (  # type: ignore[no-redef, import-not-found]
        ExceptionGroup,
    )

from dishka.text_rendering.path import PathRenderer

_renderer = PathRenderer()


class DishkaError(Exception):
    pass


class ExitError(ExceptionGroup[Exception], DishkaError):
    pass


class NoContextValueError(DishkaError):
    pass
