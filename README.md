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

This library aims to provide only an IoC container, but one that is genuinely useful.
If you're tired of manually passing objects just to create other objects that, in turn, create even more — this is the
solution for you.
Not every project requires an IoC container, but take a look at what we offer.

Unlike other tools, this one doesn't attempt to solve tasks unrelated
to [dependency injection](https://dishka.readthedocs.io/en/latest/di_intro.html).
Instead, it keeps DI in place without cluttering your code with global variables and scattered specifiers.

#### Main ideas:

* **Scopes**. Any object can have a lifespan for the entire app, a single request, or even more fractionally. Many
  frameworks either lack scopes entirely or provide only two. Here, you can define as many scopes as needed.
* **Finalization**. Some dependencies, like database connections, need not only be created but also carefully released.
  Many frameworks lack this essential feature.
* **Modular providers**. Instead of creating many separate functions or, conversely, one large class, you can
  split your factories into multiple classes, making them easier to reuse.
* **Clean dependencies**. You don't need to add custom markers to the dependency code just to make it visible to the
  library. All customization is managed by the library's own providers, so only the boundaries of scopes interact with
  the library API.
* **Simple API**. Only a minimal number of objects are needed to start using the library. Integration with your task
  framework is straightforward, with examples provided.
* **Speed**. The library is fast enough that you don't have to worry about performance. In fact, it outperforms many
  alternatives.

See more in the [technical requirements.](https://dishka.readthedocs.io/en/latest/requirements/technical.html)

### Quickstart

1. **Install dishka.**

```shell
pip install dishka
```

2. **Define your classes with type hints.** Imagine you have two classes: `Service` (a kind of business logic) and
   `DAO` (a kind of data access), along with an external API client:

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

3. **Create Provider instance**. It is only used to set up all factories that will provide your objects.

```python
from dishka import Provider

provider = Provider()
```

4. **Configure dependencies.**

We use `scope=Scope.APP` for dependencies created only once during the application's lifetime,
and `scope=Scope.REQUEST` for those that should be recreated for each processing request/event/etc.
For more details on scopes, refer to the [documentation.](https://dishka.readthedocs.io/en/latest/advanced/scopes.html)

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
        conn = sqlite3.connect()
        yield conn
        conn.close()
```

5. **Create the main `Container` instance**, passing in the providers, and step into the `APP` scope.

```python
from dishka import make_container

container = make_container(service_provider, ConnectionProvider())
```

6. **Access dependencies using the container.** The container holds a cache of dependencies and is used to retrieve
   them. Use `.get` to access APP-scoped dependencies:

```python
client = container.get(SomeClient)  # `SomeClient` has Scope.APP, so it is accessible here
client = container.get(SomeClient)  # same instance of `SomeClient`
```

7. After that, you can repeatedly **enter** and **exit the `REQUEST` scope using a context manager**:

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

8. **Close the container** when done:

```python
container.close()
```

9. **Integrate with your framework.** If you're using a supported framework, add decorators and middleware for it.
   For more details, see
   the [integration documentation.](https://dishka.readthedocs.io/en/latest/integrations/index.html)

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

If you are developing a web application, you would enter the `APP` scope on startup and enter the `REQUEST` scope for
each HTTP-request.

If the standard scope flow doesn't fit your needs, you can define your own `Scopes` class.

**Container** is what you use to get your dependencies.
You simply call `.get(SomeType)`, and it finds a way to provide you with an instance of that type.
The container itself doesn't create objects but manages their lifecycle and caches.
It delegates object creation to providers that were added during setup.

**Provider** is a collection of functions that actually provide certain objects.
A `Provider` is a class with various attributes and methods, each created through `provide`, `alias`, or
`decorate`.
These can serve as provider methods, functions to assign attributes, or method decorators.

`@provide` can be used as a decorator for a method.
This method will be called when the corresponding dependency has to be created.
The method's name is unimportant: just make sure it's different from other `Provider` attributes.
Type hints are essential: they indicate what this method creates and what it requires.
All method parameters are treated as dependencies and are created using the container.

If `provide` is applied to a class, that class itself is treated as a factory (its `__init__` parameters are analyzed).
Remember to assign this call to an attribute; otherwise, it will be ignored.

**Component** is an isolated group of providers within the same container, identified by a unique string. When a
dependency is requested, it is only searched for within the same component as the requesting object, unless explicitly
specified otherwise.

This structure allows you to build different parts of the application separately without worrying about using the same
types.
