__all__ = [
    "DependencySource",
    "alias", "Alias",
    "decorate", "Decorator",
    "provide", "Factory", "FactoryType",
]

from .alias import Alias, alias
from .decorator import Decorator, decorate
from .factory import Factory, FactoryType, provide

DependencySource = Alias | Factory | Decorator
