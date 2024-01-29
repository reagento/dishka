try:
    from builtins import ExceptionGroup
except ImportError:
    from exceptiongroup import ExceptionGroup


class DishkaException:
    pass


class InvalidGraphError(DishkaException, ValueError):
    pass


class ExitExceptionGroup(ExceptionGroup, DishkaException):
    pass
