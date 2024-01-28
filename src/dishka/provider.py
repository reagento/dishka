from typing import List

from .dependency_source import DependencySource


class Provider:
    """
    A collection of dependency sources.

    Inherit this class and add attributes using
    `provide`, `alias` or `decorate`.

    You can use `__init__`, regular methods and attributes as usual,
    they won't be analyzed when creating a container

    The only intended usage of providers is to pass them when
    creating a container
    """

    def __init__(self):
        self.dependency_sources: List[DependencySource] = [
            getattr(self, name)
            for name, attr in vars(type(self)).items()
            if isinstance(attr, DependencySource)
        ]
