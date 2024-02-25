__all__ = [
    "DependencySource",
    "alias", "Alias",
    "decorate", "Decorator",
    "provide", "Factory", "FactoryType",
]

from .alias import alias, Alias
from .decorator import decorate, Decorator
from .factory import provide, Factory, FactoryType

DependencySource = Alias | Factory | Decorator
