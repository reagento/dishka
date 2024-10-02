from dataclasses import dataclass


@dataclass
class ValidationSettings:
    nothing_overridden: bool = False
    implicit_override: bool = False


DEFAULT_VALIDATION = ValidationSettings()
STRICT_VALIDATION = ValidationSettings(
    nothing_overridden=True,
    implicit_override=True,
)
