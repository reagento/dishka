from dishka.exception_base import DishkaError


class DishkaAppError(DishkaError):
    """An invalid application lifecycle or injection context."""


class NoActiveAppError(DishkaAppError):
    def __str__(self) -> str:
        return "No active DishkaApp. Use 'with app' or 'async with app'."


class ModuleNotIncludedError(DishkaAppError):
    def __str__(self) -> str:
        return (
            "The module is not included in the active DishkaApp. "
            "Call app.include(module)."
        )


class AppAlreadyEnteredError(DishkaAppError):
    def __str__(self) -> str:
        return "A DishkaApp instance can only be entered once."


class AppScopeClosedError(DishkaAppError):
    def __str__(self) -> str:
        return "The application or call scope has already exited."


class ActiveAppScopesError(DishkaAppError):
    def __init__(self, count: int) -> None:
        self.count = count

    def __str__(self) -> str:
        return (
            f"DishkaApp exited with {self.count} active call scope(s). "
            "Finish or close all calls to complete container cleanup."
        )


class AsyncAppRequiredError(DishkaAppError):
    def __str__(self) -> str:
        return "Use 'async with' with an AsyncContainer."
