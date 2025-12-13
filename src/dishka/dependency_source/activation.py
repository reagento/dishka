from typing import Any, TypeVar, get_args, get_origin

from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from .factory import Factory
from .type_match import get_typevar_replacement, is_broader_or_same_type
from ..entities.factory_type import FactoryType


class Activation:
    __slots__ = ("factory", "provides")

    def __init__(
        self,
        factory: Factory,
        provides: DependencyKey | None = None,
    ) -> None:
        self.factory = factory
        self.provides = provides

    def is_static_evaluated(self) -> bool:
        if self.factory.type is not FactoryType.FACTORY:
            return False
        if not self.factory.dependencies:
            return True

        # TODO
        return False