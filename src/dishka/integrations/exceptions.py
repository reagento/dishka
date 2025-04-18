from dishka.exception_base import DishkaError


class InvalidInjectedFuncTypeError(DishkaError):
    def __str__(self) -> str:
        return (
            "An async container cannot be used in a synchronous context."
        )
