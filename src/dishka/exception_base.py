try:
    from builtins import (  # type: ignore[attr-defined, unused-ignore]
        ExceptionGroup,
    )

except ImportError:
    from exceptiongroup import (  # type: ignore[no-redef, import-not-found, unused-ignore]
        ExceptionGroup,
    )


class DishkaError(Exception):
    pass


class ExitError(
    ExceptionGroup[Exception],  # type: ignore[misc, unused-ignore]
    DishkaError,
):
    pass


class NoContextValueError(DishkaError):
    pass


class UnsupportedFactoryError(DishkaError):
    pass


class InvalidGraphError(DishkaError):
    pass
