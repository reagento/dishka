from dataclasses import dataclass


@dataclass
class ValidationSettings:
    # check if no factory found to override when set override=True
    nothing_overridden: bool = False
    # check if factory is overridden when set override=False
    implicit_override: bool = False


DEFAULT_VALIDATION = ValidationSettings()
STRICT_VALIDATION = ValidationSettings(
    nothing_overridden=True,
    implicit_override=True,
)
