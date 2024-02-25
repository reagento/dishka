__all__ = [
    "DependencySource",
    "alias", "Alias",
    "decorate", "Decorator",
    "provide", "Factory", "FactoryType",
    "DependencyKey",
]

from .alias import Alias, alias
from .decorator import Decorator, decorate
from .factory import Factory, FactoryType, provide
from .key import DependencyKey

DependencySource = Alias | Factory | Decorator
