from dishka.exception_base import DishkaError


class InvalidInjectedFuncTypeError(DishkaError):
    def __init__(self, func_name: str) -> None:
        self._func_name = func_name

    def __str__(self) -> str:
        return (
            "An async container cannot be used in a synchronous context"
            f" with function {self._func_name}."
        )


class ImproperProvideContextUsageError(DishkaError):
    def __str__(self) -> str:
        return "provide_context can only be used with manage_scope=True."
