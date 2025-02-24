try:
    from builtins import (  # type: ignore[attr-defined, unused-ignore]
        ExceptionGroup,
    )

except ImportError:
    from exceptiongroup import (  # type: ignore[no-redef, import-not-found, unused-ignore]
        ExceptionGroup,
    )

from dishka.text_rendering.path import PathRenderer

_renderer = PathRenderer()


class DishkaError(Exception):
    pass


class ExitError(
    ExceptionGroup[Exception],  # type: ignore[misc, unused-ignore]
    DishkaError,
):
    pass


class NoContextValueError(DishkaError):
    pass
