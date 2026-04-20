import warnings
from collections.abc import Callable, MutableMapping
from contextlib import AbstractContextManager
from threading import Lock
from types import TracebackType
from typing import Any, TypeVar, overload

from dishka.entities.component import DEFAULT_COMPONENT, Component
from dishka.entities.key import (
    CompilationKey,
    DependencyKey,
    compilation_to_dependency_key,
)
from dishka.entities.marker import Has, HasContext
from dishka.entities.scope import BaseScope, Scope
from dishka.entities.type_form import TypeForm
from dishka.provider import Provider, activate
from .container_objects import Exit
from .context_proxy import ContextProxy
from .entities.validation_settings import (
    DEFAULT_VALIDATION,
    ValidationSettings,
)
from .exceptions import (
    ChildScopeNotFoundError,
    ExitError,
    NoActiveFactoryError,
    NoChildScopesError,
    NoFactoryError,
    NoNonSkippedScopesError,
)
from .graph_builder.builder import GraphBuilder
from .provider import BaseProvider, make_root_context_provider
from .registry import Registry

T = TypeVar("T")


ExitCallable = Callable[
    [type | None, BaseException | None, TracebackType | None],
    None,
]


class Container:
    __slots__ = (
        "_cache",
        "_context",
        "_exits",
        "lock",
        "parent_closer",
        "parent_container",
        "parent_getter",
        "registry",
    )

    def __init__(
            self,
            registry: Registry,
            parent_container: "Container | None",
            context: dict[Any, Any] | None,
            lock_factory: Callable[
                [], AbstractContextManager[Any],
            ] | None,
            parent_closer: ExitCallable | None,
            parent_getter: Callable[[CompilationKey], Any] | None,
    ) -> None:
        self.registry = registry
        self._context = context
        self._cache: dict[Any, object] = {}
        self.parent_container = parent_container

        self.lock: AbstractContextManager[Any] | None
        if lock_factory is None:
            self.lock = None
        else:
            self.lock = lock_factory()
        self._exits: list[Exit] = []
        self.parent_closer = parent_closer
        self.parent_getter = parent_getter

    @property
    def scope(self) -> BaseScope:
        return self.registry.scope

    @property
    def context(self) -> MutableMapping[DependencyKey, Any]:
        warnings.warn(
            "`container.context` is deprecated",
            DeprecationWarning,
            stacklevel=2,
        )
        return ContextProxy(cache=self._cache, context=self._context)

    def __call__(
            self,
            context: dict[Any, Any] | None = None,
            lock_factory: Callable[
                [], AbstractContextManager[Any],
            ] | None = None,
            scope: BaseScope | None = None,
    ) -> "Container":
        """
        Prepare container for entering the inner scope.
        :param context: Data which will available in inner scope
        :param lock_factory: Callable to create lock instance or None
        :param scope: target scope or None to enter next non-skipped scope
        :return: context manager for inner scope
        """
        registry = self.registry.child_registry
        if registry is None:
            raise NoChildScopesError
        child = Container(
            registry,
            self,
            context,
            lock_factory,
            None,
            self._get,
        )
        if scope is None:
            while registry.scope.skip:
                registry = registry.child_registry
                if registry is None:
                    raise NoNonSkippedScopesError
                child = Container(
                    registry,
                    child,
                    context,
                    lock_factory,
                    child.__exit__,
                    child._get,
                )
        else:
            while registry.scope is not scope:
                registry = registry.child_registry
                if registry is None:
                    raise ChildScopeNotFoundError(scope, self.registry.scope)
                child = Container(
                    registry,
                    child,
                    context,
                    lock_factory,
                    child.__exit__,
                    child._get,
                )
        return child

    @overload
    def get(
            self,
            dependency_type: TypeForm[T],
            component: Component | None = DEFAULT_COMPONENT,
    ) -> T:
        ...

    @overload
    def get(
            self,
            dependency_type: Any,
            component: Component | None = DEFAULT_COMPONENT,
    ) -> Any:
        ...

    def get(
            self,
            dependency_type: Any,
            component: Component | None = DEFAULT_COMPONENT,
    ) -> Any:
        lock = self.lock
        try:
            if lock is None:
                return self._get_unlocked(
                    dependency_type if component == DEFAULT_COMPONENT
                    else DependencyKey(dependency_type, component),
                )
            with lock:
                return self._get_unlocked(
                    dependency_type if component == DEFAULT_COMPONENT
                    else DependencyKey(dependency_type, component),
                )
        except (NoFactoryError, NoActiveFactoryError) as e:
            e.scope = self.scope
            raise

    def _get(self, key: CompilationKey) -> Any:
        lock = self.lock
        if lock is None:
            return self._get_unlocked(key)
        with lock:
            return self._get_unlocked(key)

    def _get_unlocked(self, key: CompilationKey) -> Any:
        compiled = self.registry.get_compiled(key)
        if compiled is None:
            if self.parent_getter is None:
                dep_key = compilation_to_dependency_key(key)

                abstract_dependencies = (
                    self.registry.get_more_abstract_factories(dep_key)
                )
                concrete_dependencies = (
                    self.registry.get_more_concrete_factories(dep_key)
                )
                raise NoFactoryError(
                    dep_key,
                    suggest_abstract_factories=abstract_dependencies,
                    suggest_concrete_factories=concrete_dependencies,
                )
            try:
                return self.parent_getter(key)
            except NoFactoryError as ex:
                dep_key = compilation_to_dependency_key(key)
                abstract_dependencies = (
                    self.registry.get_more_abstract_factories(dep_key)
                )
                concrete_dependencies = (
                    self.registry.get_more_concrete_factories(dep_key)
                )
                ex.suggest_abstract_factories.extend(abstract_dependencies)
                ex.suggest_concrete_factories.extend(concrete_dependencies)
                raise

        return compiled(
            self.parent_getter,
            self._exits,
            self._cache,
            self._context,
            self,
            self._has,
        )

    def close(self, exception: BaseException | None = None) -> None:
        self.__exit__(None, exception, None)

    def __enter__(self) -> "Container":
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None = None,
            exception: BaseException | None = None,
            exc_tb: TracebackType | None = None,
    ) -> None:
        errors = None
        while self._exits:
            gen, _agen = self._exits.pop()
            try:
                if gen is not None:
                    gen.send(exception)
            except StopIteration:
                pass
            except Exception as err:  # noqa: BLE001
                if errors is None:
                    errors = [err]
                else:
                    errors.append(err)
        self._cache = {}
        if self.parent_closer:
            try:
                self.parent_closer(exc_type, exception, exc_tb)
            except Exception as err:  # noqa: BLE001
                if errors is None:
                    errors = [err]
                else:
                    errors.append(err)

        if errors is not None:
            raise ExitError("Cleanup context errors", errors)  # noqa: TRY003

    def _has(self, marker: CompilationKey) -> bool:
        compiled = self.registry.get_compiled_activation(marker)
        if not compiled:
            if not self.parent_container:
                return False
            return self.parent_container._has(marker)  # noqa: SLF001
        return bool(compiled(
            self._get_unlocked,
            self._exits,
            self._cache,
            self._context,
            self,
            self._has,
        ))

    def _has_context(self, marker: Any) -> bool:
        return self._context is not None and marker in self._context


class HasProvider(Provider):
    """
    This provider is used only for direct access on Has/HasContext.
    Basic implementation is inlined in code builder.
    """
    @activate(Has)
    def has(
        self,
        marker: DependencyKey,
        container: Container,
    ) -> bool:
        return container._has(  # noqa: SLF001
            marker.type_hint.value if marker.component == DEFAULT_COMPONENT
            else DependencyKey(marker.type_hint.value, marker.component),
        )

    @activate(HasContext)
    def has_context(
        self,
        marker: HasContext,
        container: Container,
    ) -> bool:
        return container._has_context(marker.value)   # noqa: SLF001


def make_container(
        *providers: BaseProvider,
        scopes: type[BaseScope] = Scope,
        context: dict[Any, Any] | None = None,
        lock_factory: Callable[[], AbstractContextManager[Any]] | None = Lock,
        skip_validation: bool = False,
        start_scope: BaseScope | None = None,
        validation_settings: ValidationSettings = DEFAULT_VALIDATION,
) -> Container:
    context_provider = make_root_context_provider(providers, context, scopes)
    has_provider = HasProvider()
    builder = GraphBuilder(
        root_context=context or {},
        scopes=scopes,
        start_scope=start_scope,
        container_key=CONTAINER_KEY,
        skip_validation=skip_validation,
        validation_settings=validation_settings,
    )
    builder.add_multicomponent_providers(has_provider)
    builder.add_providers(*providers)
    builder.add_providers(context_provider)
    registries = builder.build()
    container = Container(
        registries[0],
        context=context,
        lock_factory=lock_factory,
        parent_getter=None,
        parent_closer=None,
        parent_container=None,
    )
    if start_scope is None:
        while container.registry.scope.skip:
            if container.registry.child_registry is None:
                raise NoNonSkippedScopesError
            container = Container(
                registry=container.registry.child_registry,
                parent_container=container,
                context=context,
                lock_factory=lock_factory,
                parent_closer=container.__exit__,
                parent_getter=container._get,  # noqa: SLF001
            )
    else:
        while container.registry.scope is not start_scope:
            if container.registry.child_registry is None:
                raise ChildScopeNotFoundError(
                    start_scope,
                    container.registry.scope,
                )
            container = Container(
                registry=container.registry.child_registry,
                parent_container=container,
                context=context,
                lock_factory=lock_factory,
                parent_closer=container.__exit__,
                parent_getter=container._get,  # noqa: SLF001
            )
    return container


CONTAINER_KEY = DependencyKey(Container, DEFAULT_COMPONENT)
