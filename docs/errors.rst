Errors handling and validation
==========================================

Dishka tries to prevent most of errors so it checks dependency graph during container creation.
You can disable this behavior passing ``skip_validation=True`` to
``make_container``/``make_async_container`` functions or switch several options
setting ``validation_settings``. E.g, this will enable all currently possible validations (not all are enabled by default):


.. code-block:: python

    from dishka import make_container, ValidationSettings

    settings = ValidationSettings(
        nothing_overridden = True,
        implicit_override = True,
        nothing_decorated = True,
    )
    container = make_container(provider, validation_settings=settings)


Some of the exceptions can be raised during container creation,
some can be also raised later when some object is requested.
Here are some cases and their possible reasons

Possible errors
********************************

NoScopeSetInProvideError: No scope is set for ...
-------------------------------------------------------

.. code-block::

    dishka.provider.exceptions.NoScopeSetInProvideError: No scope is set for `__main__.A`.
    Set in provide() call for `FirstProvider.get_a` or within `__main__.FirstProvider`

Any object has some lifecycle defined by its scope.
Object cannot be created if dishka doesn't have info about its scope.

You can set it in multiple places (from lower to higher priority):

* as a parameter of ``@provide()`` decorator or ``.provide()`` method
* as a papameter when creating an instance of your provider
* within your provider as a class attribute


CycleDependenciesError: Cycle dependencies detected.
-------------------------------------------------------

.. code-block::

    dishka.exceptions.CycleDependenciesError: Cycle dependencies detected.
                ◈ Scope.APP, component='' ◈
       ╭─>─╮ __main__.A   FirstProvider.get_a
       │   ▼ __main__.B   FirstProvider.get_b
       ╰─<─╯ __main__.C   AnotherProvider.get_c


This error means that one of the objects cannot be created because some of
its dependencies depends on itself.
You can see the whole path in the error message with types and provider methods.

Possible actions:

* **Remove cycle dependency.**
  If the cycle was introduced as a result of typo you can fix it.
  But in other cases this can lead to a refactoring of your object structure

* **Implement two-phase initialization.**
  Instead of doing constructor injection using dishka you can do attribute injection later when both objects are available.


GraphMissingFactoryError: Cannot find factory for ...
-------------------------------------------------------

.. code-block::

    dishka.exceptions.GraphMissingFactoryError: Cannot find factory for (C, component=''). It is missing or has invalid scope.
       │     ◈ Scope.APP, component='' ◈
       ▼   __main__.A   FirstProvider.get_a
       ▼   __main__.B   FirstProvider.get_b
       ╰─> __main__.C   ???


There are multiple reasons for this error. If possible, dishka tries to predict possible fixes.

* **Factory is simply missing.**
  Check that you added all required providers and they contain appropriate ``provide``.

* **Context data is not marked with from_context**
  Check that you added all required providers and they contain appropriate ``from_context``.

* **Object has invalid scope**
  Check the scope of provided type and the types dependent on it.
  Note, that long-living objects cannot depend on short-living ones.
  E.g. object with ``Scope.APP`` cannot depend on one with ``Scope.REQUEST``.

  You should review used scopes.

* **Object is provided in another component**
  Components are isolated and cannot implicitly share objects.
  You should either use ``FromComponent`` to call another component directly or
  create object separately for appropriate component using ``provide`` annotation

* **Dependency is parent class while provided child class (or vice versa)**
  Use ``provives=`` argument to mark that source and provided types are different.
  Use ``WithParents[X]`` to provide an object as its type with parent classes

