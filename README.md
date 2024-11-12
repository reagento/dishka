## Dishka (stands for "cute DI" in Russian)

[![PyPI version](https://badge.fury.io/py/dishka.svg)](https://pypi.python.org/pypi/dishka)
[![Supported versions](https://img.shields.io/pypi/pyversions/dishka.svg)](https://pypi.python.org/pypi/dishka)
[![Downloads](https://img.shields.io/pypi/dm/dishka.svg)](https://pypistats.org/packages/dishka)
[![License](https://img.shields.io/github/license/reagento/dishka)](https://github.com/reagento/dishka/blob/master/LICENSE)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/reagento/dishka/setup.yml)](https://github.com/reagento/dishka/actions)
[![Doc](https://readthedocs.org/projects/dishka/badge/?version=latest&style=flat)](https://dishka.readthedocs.io)
[![Telegram](https://img.shields.io/badge/💬-Telegram-blue)](https://t.me/reagento_ru)

Cute DI framework with scopes and agreeable API.

📚 [Documentation](https://dishka.readthedocs.io)

### Purpose

This library provides **IoC container** that's genuinely useful.
If you're tired of manually passing objects just to create other objects, which then create even more — this is for
you.
Not every project requires an IoC container, but take a look at what we offer.

Unlike other tools, this one focuses **only**
on [dependency injection](https://dishka.readthedocs.io/en/latest/di_intro.html), without trying to solve unrelated
tasks.
It keeps DI in place without cluttering your code with global variables and scattered specifiers.

To see how Dishka **stands out** among other dependency injection tools, check out
the [detailed comparison](https://dishka.readthedocs.io/en/latest/alternatives.html) highlighting its unique
advantages.

#### Key features:

* **Scopes**. Any object can have a lifespan for the entire app, a single request, or even more fractionally. Many
  frameworks either lack scopes entirely or offer only two. Here, you can define as many scopes as needed.
* **Finalization**. Some dependencies, like database connections, need not only to be created but also carefully
  released. Many frameworks lack this essential feature.
* **Modular providers**. Instead of creating many separate functions or one large class, you can split factories
  into smaller classes for easier reuse.
* **Clean dependencies**. You don't need to add custom markers to dependency code just to make it visible to the
  library. Customization is managed by the library's providers, so only scope boundaries interact with the library API.
* **Simple API**. Only a few objects are needed to start using the library. Integration with your framework is
  straightforward, with examples provided.
* **Speed**. The library is fast enough that performance is not a concern. In fact, it outperforms many
  alternatives.

See more in [technical requirements.](https://dishka.readthedocs.io/en/latest/requirements/technical.html)

### Quickstart

1. **Install dishka.**

```shell
pip install dishka
```

2. **Define your classes with type hints.** Imagine you have two classes: `Service` (business logic) and
   `DAO` (data access), along with an external API client:

```python
class DAO(Protocol):
    ...


class Service:
    def __init__(self, dao: DAO):
        ...


class DAOImpl(DAO):
    def __init__(self, connection: Connection):
        ...


class SomeClient:
    ...
```

3. **Create Provider** instance and set up how to provide dependencies.

Providers are used only to set up factories providing your objects.

Use `scope=Scope.APP` for dependencies created once per application lifetime,
and `scope=Scope.REQUEST` for those that need to be recreated for each request, event, etc.
To learn more about scopes, see [documentation.](https://dishka.readthedocs.io/en/latest/advanced/scopes.html)

```python
from dishka import Provider, Scope

service_provider = Provider(scope=Scope.REQUEST)
service_provider.provide(Service)
service_provider.provide(DAOImpl, provides=DAO)
service_provider.provide(SomeClient, scope=Scope.APP)  # override provider scope
```

To provide a connection, you might need some custom code:

```python
from dishka import Provider, provide, Scope


class ConnectionProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def new_connection(self) -> Iterable[Connection]:
        conn = sqlite3.connect(":memory:")
        yield conn
        conn.close()
```

4. **Create main `Container`** instance by passing providers, and enter `APP` scope.

```python
from dishka import make_container

container = make_container(service_provider, ConnectionProvider())
```

5. **Access dependencies using container.** Container holds a cache of dependencies and is used to retrieve them.
   You can use `.get` method to access `APP`-scoped dependencies:

```python
client = container.get(SomeClient)  # `SomeClient` has Scope.APP, so it is accessible here
client = container.get(SomeClient)  # same instance of `SomeClient`
```

6. **Enter and exit `REQUEST` scope repeatedly using a context manager**:

```python
# subcontainer to access shorter-living objects
with container() as request_container:
    service = request_container.get(Service)
    service = request_container.get(Service)  # same service instance
# at this point, the connection will be closed as we exit the context manager

# new subcontainer with a new lifespan for request processing
with container() as request_container:
    service = request_container.get(Service)  # new service instance
```

7. **Close container** when done:

```python
container.close()
```

8. **Integrate with your framework.** If you are using a supported framework, add decorators and middleware for it.
   For more details, see [integrations doc.](https://dishka.readthedocs.io/en/latest/integrations/index.html)

```python
from dishka.integrations.fastapi import (
    FromDishka, inject, setup_dishka,
)


@router.get("/")
@inject
async def index(service: FromDishka[Service]) -> str:
    ...


...
setup_dishka(container, app)
```

### Concepts

**Dependency** is what you need for some parts of your code to work.
Dependencies are simply objects you don't create directly in place and might want to replace someday, at least for
testing purposes.
Some of them live throughout your application's runtime, while others are created and destroyed with each request.
Dependencies can also rely on other objects, which then become their dependencies.

**Scope** is the lifespan of a dependency. The standard scopes are (with some skipped):

`APP` -> `REQUEST` -> `ACTION` -> `STEP`.

You decide when to enter and exit each scope, but this happens one by one.
You assign a scope to each dependency when configuring its creation.
By default, if the same dependency is requested multiple times within a single scope without leaving it, the same
instance is returned.

For a web application, enter `APP` scope on startup and `REQUEST` scope for each HTTP request.

If the standard scope flow doesn't fit your needs, you can define your own `Scopes` class.

**Container** is what you use to get your dependencies.
You simply call `.get(SomeType)`, and it finds a way to provide you with an instance of that type.
The container itself doesn't create objects but manages their lifecycle and caches.
It delegates object creation to providers added during setup.

**Provider** is a collection of functions that actually provide certain objects.
A `Provider` is a class with various attributes and methods, each created through `provide`, `alias`, or
`decorate`.
These can serve as provider methods, functions to assign attributes, or method decorators.

`@provide` can be used as a decorator for a method.
This method will be called when the corresponding dependency has to be created.
Method name is unimportant: just make sure it's different from other `Provider` attributes.
Type hints are crucial: they indicate what this method creates and what it requires.
All method parameters are treated as dependencies and are created using the container.

If `provide` is applied to a class, that class itself is treated as a factory (its `__init__` parameters are analyzed).
Remember to assign this call to an attribute; otherwise, it will be ignored.

**Component** is an isolated group of providers within the same container, identified by a unique string. When a
dependency is requested, it is only searched for within the same component as the requesting object, unless explicitly
specified otherwise.

This structure allows you to build different parts of the application separately without worrying about using the same
types.
