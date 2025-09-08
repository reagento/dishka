Errors handling and validation
==========================================

Configuration
********************************

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
Here are some cases and their possible reasons.

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
* as a parameter when creating an instance of your provider
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
its dependencies depend on itself.
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
  Use ``provides=`` argument to mark that source and provided types are different.
  Use ``WithParents[X]`` to provide an object as its type with parent classes


CannotUseProtocolError: Cannot use ... as a factory
-------------------------------------------------------

.. code-block::

    dishka.provider.exceptions.CannotUseProtocolError: Cannot use <class '__main__.SomeProtocol'> as a factory.
    Tip: seems that this is a Protocol. Please subclass it and provide the subclass.

This error means that you used some protocol class as a source argument of ``provide`` function.
Protocols cannot be instantiated.
Check that you have an implementation for that protocol, and use it.
You can try using the form ``provide(YourImpl, provides=YourProtocol)``.


NotAFactoryError: Cannot use ... as a factory.
-------------------------------------------------------

.. code-block::

    dishka.provider.exceptions.NotAFactoryError: Cannot use typing.Union[int, str] as a factory.


Check what are you passing to ``provide`` function. Probably that object cannot be instantiated directly.

Note, that you can provide some type by creating an instance of another one using the form ``provide(YourClass, provides=SomeTypeHint)``.


ImplicitOverrideDetectedError: Detected multiple factories for ...
-------------------------------------------------------------------------

.. code-block::

    dishka.exceptions.ImplicitOverrideDetectedError: Detected multiple factories for (<class '__main__.A'>, component='') while `override` flag is not set.
    Hint:
    * Try specifying `override=True` for SecondProvider.get_a
    * Try removing factory FirstProvider.get_a or SecondProvider.get_a

This error can be seen only if you enabled ``implicit_override=True`` in validation settings.
It means that you have 2 factories for the same type without specifying that the second one should replace the first one.

* **You meant to have one of factories**. Just remove the second one.

* **You want to override dependency for tests or other purposes**. Specify ``override=True`` when creating second factory.

Error text will contain details on both option with names of providers.


NothingOverriddenError: Overriding factory found for ..., but there is nothing to override.
---------------------------------------------------------------------------------------------------

.. code-block::

    dishka.exceptions.NothingOverriddenError: Overriding factory found for (<class '__main__.A'>, component=''), but there is nothing to override.
    Hint:
    * Try removing override=True from FirstProvider.get_a
    * Check the order of providers

This error can be seen only if you enabled ``nothing_overridden=True`` in validation settings.
That means you set ``override=True``, but there is no second factory to be overriden or the order of providers is incorrect.

Check, that you have specified all expected providers in correct order or remove the flag.


IndependentDecoratorError: Decorator ... does not depend on provided type.
---------------------------------------------------------------------------------------------------

.. code-block::

    dishka.provider.exceptions.IndependentDecoratorError: Decorator __main__.FirstProvider.get_a does not depend on provided type.
    Did you mean @provide instead of @decorate?

Using ``decorate`` is a special case if you need to apply decorator patter or do modifications with an object created in another provider.
Is requests an object of some type (additional dependencies are allowed) and returns the same type.

If you are not going to use an object received from another factory, probably you meant to use simple ``provide`` instead?
