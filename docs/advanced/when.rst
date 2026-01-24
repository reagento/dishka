Conditional activation
============================================

There are some cases when you want to declare a factory or decorator in a provider but use only when a certain condition is met. For example:

* Apply decorators in debug mode
* Use cache if redis config provided in context
* Implement A/B testing with different implementations based on HTTP header
* Provide different identity provider classes based on available context objects: web request or queued messages.

This can be achieved with "activation" approach. Key concepts here:

* **Marker** - special object to distinguish which implementations should be used.
* **Activator** or **activation function** - special function registered in provider and taking decision if marker is active or not.
* **activation condition** - expression with marker objects set in dependency source dynamically associated with activators to select between multiple implementations or enable decorators


.. note::

    The activation feature makes the application harder to analyze and can also affect performance, so use it wisely.

Basic usage
---------------------------------

To set conditional activation you create special ``Marker`` objects and use them in ``when=`` condition inside ``provide``, ``decorate`` or ``alias``.

.. code-block:: python

    from dishka import Provider, provide, Scope

    class MyProvider(Provider)
        @provide(scope=Scope.APP)
        def base_impl(self) -> Cache:
            return NormalCacheImpl()

        @provide(when=Marker("debug"), scope=Scope.APP)
        def debug_impl(self) -> Cache:
            return DebugCacheImpl()

In this code you can see 2 factories providing same type ``Cache``.
The second one is used whenever ``Marker("debug")`` is treated as as active.
The base implementation will be used in all other cases as it has no condition set.
The overall rule is "last wins" like it worked with overriding.

Second step is to provide logic of marker activation. You write a function returning ``bool`` and register it in provider using ``@activate`` decorator.
It can be the same or another provider while you pass when creating a container.

.. code-block:: python

    from dishka import activate, Provider

    class MyProvider(Provider)
        @activate(Marker("debug"))
        def is_debug(self) -> bool:
            return False

This function can use other objects as well. For example, we can pass config using context

.. code-block:: python

    class MyProvider(Provider)
        config = from_context(Config, scope=Scope.APP)

        @activate(Marker("debug"))
        def is_debug(self, config: Config) -> bool:
            return config.debug

Activation on marker type
--------------------------------

More general pattern is to create own marker type and register a single activator on all instances. You can request marker as an activator parameter.

.. code-block::

    class EnvMarker(Marker):
        pass


    class MyProvider(Provider)
        config = from_context(Config, scope=Scope.APP)

        @activate(EnvMarker)
        def is_debug(self, marker: EnvMarker, config: Config) -> bool:
            return config.environment == marker.value


Combining markers
------------------------------------------

Markers support simple combination logic when used in ``when=`` using ``|`` (or), ``&`` (and) and ``~`` (not) operators

.. code-block:: python


        @provide(when=Marker("debug") | EnvMarker("preprod"))
        def debug_impl(self) -> Cache:
            return DebugCacheImpl()

        @provide(when=~Marker("debug") & EnvMarker("preprod"))
        def test_impl(self) -> Cache:
            return TestCacheImpl()


Provider-level activation
-------------------------

You can set ``when=`` on the entire provider to apply a condition to all factories, aliases, and decorators within it. This reduces boilerplate when all dependencies in a provider share the same activation condition.

.. code-block:: python

    from dishka import Marker, Provider, Scope, provide

    class DebugProvider(Provider):
        when = Marker("debug")
        scope = Scope.APP

        @provide
        def debug_cache(self) -> Cache:
            return DebugCacheImpl()

        @provide
        def debug_logger(self) -> Logger:
            return VerboseLogger()

The provider's ``when`` can also be set via constructor:

.. code-block:: python

    provider = DebugProvider(when=Marker("debug"))

When both provider and individual source have ``when=``, conditions are combined with AND logic:

.. code-block:: python

    class FeatureProvider(Provider):
        when = Marker("prod")  # prerequisite
        scope = Scope.APP

        @provide(when=Has(RedisConfig))  # additional condition
        def redis_cache(self, config: RedisConfig) -> Cache:
            return RedisCache(config)
        # Effective: Marker("prod") & Has(RedisConfig)

The provider's ``when`` acts as a prerequisite; individual sources add further constraints. If a factory shouldn't inherit the provider's condition, move it to a different provider.

Checking graph elements
---------------------------------------

In case you want to activate some features when specific objects are available you can use ``Has`` marker. It checks whether

* requested class is registered in container with appropriate scope
* it is activated
* if it actually presents in context while being registered as ``from_context``


For example:

.. code-block:: python

    from dishka import Provider, provide, Scope

    class MyProvider(Provider)
        config = from_context(RedisConfig, scope=Scope.APP)

        @provide(scope=Scope.APP)
        def base_impl(self) -> Cache:
            return NormalCacheImpl()

        @provide(when=Has(RedisConfig), scope=Scope.APP)
        def redis_impl(self, config: RedisConfig) -> Cache:
            return RedisCache(config)

        @provide(when=Has(MemcachedConfig), scope=Scope.APP)
        def memcached_impl(self, config: MemcachedConfig) -> Cache:
            return MemcachedCache(config)


    container = make_container(MyProvider, context={})


In this case,

* ``memcached_impl`` is not used because no factory for ``MemcachedConfig`` is provided
* ``redis_impl`` is not used while it is registered as ``from_context`` but no real value is provided.
* ``base_impl`` is used as a default one, because none of later is active