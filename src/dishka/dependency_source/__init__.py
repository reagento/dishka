__all__ = [
    "DependencySource",
    "alias", "Alias",
    "context_var", "from_context",
    "decorate", "Decorator",
    "provide", "Factory", "FactoryType",
]

from .alias import Alias, alias
from .context_var import ContextVariable, from_context
from .decorator import Decorator, decorate
from .factory import Factory, FactoryType, provide

DependencySource = Alias | Factory | Decorator | ContextVariable
