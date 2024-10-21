dishka
=============================================

Cute DI framework with scopes and agreeable API.

This library is targeting to provide only an IoC-container but make it really useful.
If you are tired manually passing objects to create others objects which are only used to create more objects - we have a solution.

Unlike other instruments we are not trying to solve tasks not related to dependency injection. We want to keep DI in place, not soiling you code with global variables and additional specifiers in all places.

Main ideas:

* **Scopes**. Any object can have lifespan of the whole app, single request or even more fractionally. Many frameworks do not have scopes or have only 2 of them. Here you can have as many scopes as you need.
* **Finalization**. Some dependencies like database connections must be not only created, but carefully released. Many framework lack this essential feature
* **Modular providers**. Instead of creating lots of separate functions or contrariwise a big single class, you can split your factories into several classes, which makes them simpler reusable.
* **Clean dependencies**. You do not need to add custom markers to the code of dependencies so to allow library to see them. All customization is done within providers code and only borders of scopes have to deal with library API.
* **Simple API**. You need minimum of objects to start using library. You can easily integrate it with your task framework, examples provided.
* **Speed**. It is fast enough so you not to worry about. It is even faster than many of the analogs.


.. toctree::
   :hidden:
   :caption: Contents:

   quickstart
   di_intro
   concepts
   provider/index
   container/index
   integrations/index
   alternatives

.. toctree::
   :hidden:
   :caption: Advanced usage:

   advanced/components
   advanced/context
   advanced/generics
   advanced/scopes
   advanced/testing/index
   advanced/plotter

.. toctree::
   :hidden:
   :caption: For developers:

   requirements/technical
   contributing

.. toctree::
    :hidden:
    :caption: Project Links

    GitHub <https://github.com/reagento/dishka>
    PyPI <https://pypi.org/project/dishka>
    Chat <https://t.me/reagento_ru>
