Alternatives
*********************

**Dishka** was developed according to the needs of real applications. Available features were described in other parts of documentation like :ref:`technical-requirements`. But there are other libraries on the market.

For this analysis we imagined several cases. Not all applications require all of them, but they might be needed at some point in their lifetime:

* For some apps (like AWS Lambdas) you do not need to create all singletons at startup as it serves only few requests.
* For some apps (like desktop) you will use threads, for others you will use asyncio
* Some objects such as database connections may require async initialization and finalization.
* Some dependencies must be shared between other objects. For example: databases connection can be used by multiple data-mappers and unit-of-work within single processing request.

Actually, everything can be done in your code: DI-framework is not a required thing for an application. But isn't it more pleasure when everything is just working out of the box?

There might be errors in this comparison, some features are not well described while still exist in selected libraries. Some features can be implemented manually, but this topic is not about your code - it is about existing libraries.

Overview
===========================

.. list-table:: IoC-containers
   :header-rows: 1

   * -
     - :abbr:`Scopes(Separate cache for each "request"; additional scopes)`
     - :abbr:`Async support`
     - :abbr:`Finalization(Dependencies correctly automatically finalized on scope exit)`
     - :abbr:`Concurrency-safe(Thread-safety and async task-safety)`
     - :abbr:`Auto-wiring(Simplified registration of classes based on their init)`
     - Context data
     - :abbr:`Zero-globals(Can be used without global state)`
   * - `dishka <https://github.com/ragento/dishka>`_
     - ✅✅
     - ✅
     - ✅
     - ✅
     - ✅✅
     - ✅
     - ✅
   * - `di <https://github.com/adriangb/di>`_
     - ✅✅
     - ✅
     - ✅
     - ❌
     - ✅
     - ✅
     - ✅
   * - `Fastapi Depends <https://fastapi.tiangolo.com>`_
     - ✅❌
     - ✅
     - ✅
     - :abbr:`➖(Not applicable)`
     - ✅
     - ❌
     - ✅
   * - `dependency-injector <https://github.com/ets-labs/python-dependency-injector>`_
     - ❌
     - ❌
     - ❌
     - ❌
     - ❌
     - ✅
     - ❌
   * - `injector <https://github.com/python-injector/injector>`_
     - ✅✅
     - ❌
     - ❌
     - ✅
     - ✅
     - ❌
     - ✅
   * - `svcv <https://github.com/hynek/svcs>`_
     - ❌
     - ✅
     - ✅
     - ❌
     - ❌
     - ✅
     - ✅
   * - `rodi <https://github.com/Neoteroi/rodi>`_
     - ✅❌
     - ❌
     - ❌
     - ❌
     - ✅
     - ✅
     - ✅
   * - `punq <https://github.com/bobthemighty/punq>`_
     - ✅❌
     - ❌
     - ❌
     - :abbr:`➖(Not applicable)`
     - ✅
     - ✅
     - ✅
   * - `lagom <https://github.com/meadsteve/lagom>`_
     - ❌
     - ✅
     - ✅
     - ✅
     - ✅
     - ❌
     - ❌

**Description:**

- **Scopes** - whether a container can cache dependencies per-scope. First tick is for request-scope. Second one is for supporting additional scopes. Libraries often have their own interpretation of that feature, especially if they do not offer finalization, so we count all them as equal.
- **Async support** means async functions as factories.
- **Finalization** means whether container can finalize requested dependencies (including dependencies of dependencies) after use. Often is done by scope exit.
- **Concurrency-safe** means if singletons and scope cache is safe for threaded application or with multiple asyncio tasks. Not applicable if container does not provide caching or singleton patterns.
- **Autowiring** here means that you do not need copy signature of ``__init__`` method to declare dependency, or explicitly link it with other factories. Second tick is placed if you can create isolated sub-graphs still being autowired.
- **Context data** is additional data which is passed to dependency factories after container creation. For example, HTTP-request can be used for creating Request-scoped objects.
- **Zero-globals** means real dependency injection. If dependencies are requested using some global variable (sometimes hidden inside framework) then there is no DI, but just complex factories. Container must be designed as a variant of abstract factory pattern and multiple (very different) implementations must be possible.


Why not dependency-injector?
=======================================

Though dependency-injector is quite popular project it not quite solving IoC-container tasks.

* No auto-wiring for classes is supported. You have to bind factories to each other explicitly.
* It does not cache created dependencies per-request. You have to implement it manually by using thread-locals or recreating container each time.
* Finalization is supported only for singleton resources or when using ``inject`` decorator. So you probably need to recreate container.
* Singletons are not thread-safe.
* Dependency graph is badly customizable. You can only replace dependency providers once you declare them all.
* When injecting dependencies in functions you rely on container with all specified providers. Additionally, it implicitly uses global container, which can be a problem in concurrent tests.
* It has a quite complex API, which is mostly declares an alternative way of calling functions


Why not injector?
=======================

Injector is a quite popular tool with long history, but it has very few features and main examples propose not the best ways of using it.

* You can add scopes there, but there is no management: you have to write own logic. Out of the box you have singletons and thread-locals.
* No asyncio support
* No resource finalization
* It is quite slow. We find it x20 slower than ``dishka``.
* Auto-wiring is implemented. You are not obligated to bind each class to container: it can be useful in some cases, but makes more difficult to find classes with wrong scope.



Why not di?
======================

``di`` is a young promising project which has own advantages comparing to dishka, but looks more complicated.

* You need to pass 3 things to get a dependency: solved dependency, executor and state. In dishka you need only container (and already known dependency type).
* Scopes in di work differently, they are not thread-safe.
* It supports binding by subclasses or by name, but retrieving dependencies is more complicated.
* It does not support generic dependencies.
* It is quite fast in creating dependencies, but very slow initialization. For big graphs it can take years to start application. E.g.: if you have graph of 60 classes nested with with depth of 6, then for ``di`` it take **50 sec** to initialize container and only **5ms** for ``dishka``
* There is auto-wiring, but you cannot create isolated sub-graphs (components in ``dishka``) in case of duplicated types.
* There are no framework integrations out of the box

Why not Fastapi?
=========================

Fastapi depends provides simple but effective API to inject dependencies, but there are downsides:

* It can be used only inside fastapi.
* You cannot use it for lazy initialization of singletons
* It mixes up Dependency Injection and Request decomposition. That leads to incorrect openapi specification or even broken app.
* You have to declare each dependency with ``Depends`` on each level of application. So either your business logic contains details of IoC-container or you have to duplicate constructor signatures.
* It is not very fast in runtime, though you might never notice that
* Almost all examples in documentation ignore ``dependency_overrides``, which is actually a main thing to use fastapi as IoC-container.

Why not svcs?
======================

On first approach ``dishka`` and ``svcs`` have similar api, but ``svcs`` does much less automation:

1. In svcs all binding between classes is done manually by calling ``container`` inside each factory. In dishka you can just add class if you have type-hinted its ``__init__``. Additionally, in ``svsc`` you cannot use this information to validate graph or somehow visualize.
2. While ``svsc`` caches dependencies there is no scope hierarchy. You can create multiple containers to make lazy singletons, but they are not thread-safe.
3. There are no predefined patterns like multiple providers and class-based providers. So the only way to make your container modular you need to decide how to do it. With ``dishka`` you can reuse ``providers`` making different combinations for different environments or cases.

Why not rodi?
=============================

``Rodi`` is pretty simple and fast. Though it misses most of the useful features.

* It has auto-wiring, but no isolated components.
* No resources finalization. You can somehow track what to finalize using your instance of ``ActivationScope``, but you have to write it on your own.
* No ``async`` support.
* Documentation is mostly describing how to use it with ``blacksheep``
* There is actually 3 types of scopes: singletons, scoped and transient (``cache=False`` in dishka). In dishka you can have you own number of scopes.
* Lazy singletons are not thread safe.
* Context data can be passed using ``ActivationScope``, but anyway you need to create some factory for that dependency. In ``dishka`` there is special marker ``from_context``.

Why not ...?
==============================

There are a lot of instruments in the world and we cannot compare with all of them. Some of them have specific features, some do only the basics. Most of the tools we've seen have nothing to offer better than simple function call.

We are open to new proposals and we are investigating how to improve the experience of using the library even more.
