DishkaApp
=========

``DishkaApp`` injects dependencies into ordinary functions and methods and
manages their lifetime. ``DishkaModule`` groups injectable entry points so
that they can be declared separately from application assembly.

The complete example is in ``examples/dishka_app.py``. Run it from the repository
root with ``python -m examples.dishka_app``.

Application dependencies
------------------------

As in the framework examples, an ``Interactor`` depends on a ``DbGateway``.
Neither class needs to know about dependency injection:

.. literalinclude:: ../examples/dishka_app.py
   :language: python
   :start-at: class DbGateway
   :end-before: # app dependency logic

Register the gateway implementation and interactor using providers:

.. literalinclude:: ../examples/dishka_app.py
   :language: python
   :start-at: class AdaptersProvider
   :end-at: interactor = provide

Declare entry points
--------------------

Mark dependencies with ``FromDishka`` and decorate entry points with
``@module.inject``:

.. literalinclude:: ../examples/dishka_app.py
   :language: python
   :start-at: handlers = DishkaModule()
   :end-before: # application assembly

A module stores declarations, not a container or a reference to an application.
It can be reused by independent applications, including concurrent applications.
For static and class methods, put ``@staticmethod`` or ``@classmethod`` above
``@handlers.inject``.

Assemble and run
----------------

Create a container locally, include the module, and enter the application:

.. literalinclude:: ../examples/dishka_app.py
   :language: python
   :start-at: def main()
   :end-at: print(Commands().report())

The functions are called directly, including functions imported before
``include``. Calling an entry point outside an active application, or without
including its module in that application, raises an error.

For a small program, ``@app.inject`` can be used without a separate module.
``app.include(module)`` can be called before or inside the application block;
including the same module twice is harmless.

Lifetime and scopes
-------------------

``DishkaApp`` takes ownership of the supplied container and closes it when
the application block exits, including when an exception occurs. An application
instance can be entered only once. Do not share its container with another
application that manages its lifetime.

Each outermost entry point call opens the next non-skipped scope below the
container's current scope. With the default scopes this is ``Scope.REQUEST``.
The call scope is closed when the function returns or raises. Dependencies
belonging to ``Scope.APP`` remain available until the application exits.
Do not return scoped resources for use after their scope has closed.

Nested decorated calls in the same application reuse the current call scope,
including when the outer function has no injected parameters. An explicit
``@module.inject(scope=Scope.ACTION)`` opens the specified child scope instead.
Custom ``BaseScope`` hierarchies are supported.

To supply context data from ordinary arguments, pass a callback accepting
``(args, kwargs)``:

.. code-block:: python

    @handlers.inject(
        provide_context=lambda args, kwargs: {Job: args[0]},
    )
    def process_job(job: Job, interactor: FromDishka[Interactor]) -> str:
        return interactor()

The provider can declare ``Job`` using ``from_context`` in the call scope.
Specifying ``provide_context`` opens a new child scope, even for a nested call;
use ``scope=...`` to choose that child explicitly.

Asynchronous applications
-------------------------

Use ``async with`` for an asynchronous container and await entry points:

.. code-block:: python

    @handlers.inject
    async def index(interactor: FromDishka[Interactor]) -> str:
        return interactor()

    async def main() -> None:
        container = make_async_container(
            AdaptersProvider(), InteractorProvider(),
        )
        async with DishkaApp(container) as app:
            app.include(handlers)
            result = await index()

An asynchronous container requires asynchronous entry points. A synchronous
container supports both synchronous and asynchronous entry points, and can
also be managed using ``async with``. Asynchronous resources are finalized on
normal completion, exceptions, and cancellation.

Application and call contexts use ``ContextVar``. Independent tasks that call
entry points from the application block get separate call scopes. Tasks created
inside an entry point inherit its call scope: await them before that entry point
returns. Likewise, finish all tasks before exiting the application. A call
using an inherited scope that has already exited raises an error.

Exiting an application while an independently running call or generator still
owns a scope raises an error instead of closing ``Scope.APP`` resources before
their children. The application is immediately deactivated, so no new calls
can start. Its root container is closed automatically after the remaining call
finishes or the generator is explicitly closed.

Threads do not automatically inherit the active application context. Activate
an independent application in each thread, or explicitly propagate the context
while respecting the container's synchronization requirements.

Nested application blocks temporarily select the inner application; exiting
the inner block restores the outer one. The inner application must include
every module it uses.

Generators
----------

Generator entry points keep their call scope open until exhaustion or explicit
closure. The scope is active only while the generator executes, not in the
consumer between iterations. Consume and close generators inside the application
block. When stopping iteration early, use ``contextlib.closing`` or
``contextlib.aclosing`` so that resources are released deterministically.
Synchronous generators preserve ``send``, ``throw`` and their return value.
Asynchronous generators preserve ``asend`` and ``athrow``.

Typing and design
-----------------

The decorator preserves runtime metadata and exposes a signature without
injected parameters. Its static return type is ``Callable[..., T]``: the return
type is preserved, but static checkers cannot validate the remaining arguments.
Python typing cannot generally subtract arbitrary injected parameters from a
callable signature.

Use injection at scope boundaries, such as commands and job entry points.
Construct internal services through providers and keep their implementation
independent of injection decorators.
