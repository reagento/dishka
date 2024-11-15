dishka
=============================================

Cute DI framework with scopes and agreeable API.

This library provides **IoC container** that's genuinely useful.
If you're exhausted from endlessly passing objects just to create other objects, only to have those objects create even
more — you're not alone, and we have a solution.
Not every project requires IoC container, but take a look at what we offer.

Unlike other tools, Dishka focuses **only**
on dependency injection without trying to solve unrelated tasks.
It keeps DI in place without cluttering your code with global variables and scattered specifiers.

Key features:

* **Scopes**. Any object can have a lifespan for the entire app, a single request, or even more fractionally. Many
  frameworks either lack scopes completely or offer only two. Here, you can define as many scopes as needed.
* **Finalization**. Some dependencies, like database connections, need not only to be created but also carefully
  released. Many frameworks lack this essential feature.
* **Modular providers**. Instead of creating many separate functions or one large class, you can split factories
  into smaller classes for easier reuse.
* **Clean dependencies**. You don't need to add custom markers to dependency code just to make it visible to the
  library. Customization is managed by library providers, so only scope boundaries interact with the library API.
* **Simple API**. Only a few objects are needed to start using the library. Integration with your framework is
  straightforward, with examples provided.
* **Speed**. The library is fast enough that performance is not a concern. In fact, it outperforms many
  alternatives.

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
