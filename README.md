## dishka (stands for "cute DI" in Russian)

[![PyPI version](https://badge.fury.io/py/dishka.svg)](https://pypi.python.org/pypi/dishka)
[![Supported versions](https://img.shields.io/pypi/pyversions/dishka.svg)](https://pypi.python.org/pypi/dishka)
[![Downloads](https://img.shields.io/pypi/dm/dishka.svg)](https://pypistats.org/packages/dishka)
[![License](https://img.shields.io/github/license/reagento/dishka)](https://github.com/reagento/dishka/blob/master/LICENSE)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/reagento/dishka/setup.yml)](https://github.com/reagento/dishka/actions)
[![Doc](https://readthedocs.org/projects/dishka/badge/?version=latest&style=flat)](https://dishka.readthedocs.io)
[![Telegram](https://img.shields.io/badge/💬-Telegram-blue)](https://t.me/reagento_ru)

Cute DI framework with scopes and an agreeable API.

📚 [Documentation](https://dishka.readthedocs.io)

### Purpose

This library provides an **IoC container** that's genuinely useful.
If you're exhausted from endlessly passing objects to create other objects, only to have those objects create even
more — you're not alone, and ``dishka`` is a solution.
Not every project requires an IoC container, but take a look at what ``dishka`` offers.

Unlike other tools, ``dishka`` focuses **only**
on [dependency injection (DI)](https://dishka.readthedocs.io/en/latest/di_intro.html) without trying to solve unrelated
tasks.
It keeps DI in place without cluttering your code with global variables and scattered specifiers.

To see how ``dishka`` **stands out** among other DI tools, check out
the [detailed comparison](https://dishka.readthedocs.io/en/latest/alternatives.html).

#### Key features:

* **Scopes**. Any object can have a lifespan for the entire app, a single request, or even more fractionally. Many
  frameworks either lack scopes completely or offer only two. With ``dishka``, you can define as many scopes as needed.
* **Finalization**. Some dependencies, like database connections, need not only to be created but also carefully
  released. Many frameworks lack this essential feature.
* **Modular providers**. Instead of creating many separate functions or one large class, you can split factories
  into smaller classes for easier reuse.
* **Clean dependencies**.  You don't need to add custom markers to dependency code to make it visible for the library.
* **Simple API**. Only a few objects are needed to start using the library.
* **Framework integrations**. Popular frameworks are supported out of the box. You can simply extend it for your needs.
* **Speed**. The library is fast enough that performance is not a concern. In fact, it outperforms many
  alternatives.

See more in [technical requirements.](https://dishka.readthedocs.io/en/latest/requirements/technical.html)

### Quickstart

1. **Install dishka.**

```shell
pip install dishka
```

2. **Define classes with type hints.** Let's have the ``Service`` class (business logic) that has
two infrastructure dependencies: ``APIClient`` and ``UserDAO``. ``UserDAO`` is implemented in
``SQLiteUserDAO`` that has its own dependency - ``sqlite3.Connection``.

We want to create an ``APIClient`` instance once during the application's lifetime
and create ``UserDAO`` implementation instances on every request (event) our application handles.

```python
from sqlite3 import Connection
from typing import Protocol


class APIClient:
    ...


class UserDAO(Protocol):
    ...


class SQLiteUserDAO(UserDAO):
    def __init__(self, connection: Connection):
        ...


class Service:
    def __init__(self, client: APIClient, user_dao: UserDAO):
        ...
```

3. **Create providers** and specify how to provide dependencies.

Providers are used to set up factories for your objects. 
To learn more about providers, see [Provider](https://dishka.readthedocs.io/en/stable/provider/index.html).

Use ``Scope.APP`` for dependencies that should be created once for the entire application lifetime,
and ``Scope.REQUEST`` for those that should be created for each request, event, etc.
To learn more about scopes, see [Scope management](https://dishka.readthedocs.io/en/stable/advanced/scopes.html).

There are multiple options for registering dependencies. We will use:

* class (for ``Service`` and ``APIClient``)
* specific interface implementation (for ``UserDAO``)
* custom factory with finalization (for ``Connection``, as we want to make it releasable)

```python
import sqlite3
from collections.abc import Iterable
from sqlite3 import Connection

from dishka import Provider, Scope, provide

service_provider = Provider(scope=Scope.REQUEST)
service_provider.provide(Service)
service_provider.provide(SQLiteUserDAO, provides=UserDAO)
service_provider.provide(APIClient, scope=Scope.APP)  # override provider's scope


class ConnectionProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def new_connection(self) -> Iterable[Connection]:
        connection = sqlite3.connect(":memory:")
        yield connection
        connection.close()
```

4. **Create a container**, passing providers. You can combine as many providers as needed.

Containers hold a cache of dependencies and are used to retrieve them.
To learn more about containers, see [Container](https://dishka.readthedocs.io/en/stable/container/index.html).

```python
from dishka import make_container


container = make_container(service_provider, ConnectionProvider())
```

5. **Access dependencies using the container.**

Use the ``.get()`` method to access *APP*-scoped dependencies.
It is safe to request the same dependency multiple times.

```python
# APIClient is bound to Scope.APP, so it can be accessed here
# or from any scope inside including Scope.REQUEST
client = container.get(APIClient)
client = container.get(APIClient)  # the same APIClient instance as above
```

To access the *REQUEST* scope (sub-container) and its dependencies, use a context manager.
Higher level scoped dependencies are also available from sub-containers, e.g. ``APIClient``.

```python
# A sub-container to access shorter-living objects
with container() as request_container:
    # Service, UserDAO implementation, and Connection are bound to Scope.REQUEST,
    # so they are accessible here. APIClient can also be accessed here
    service = request_container.get(Service)
    service = request_container.get(Service)  # the same Service instance as above

# Since we exited the context manager, the sqlite3 connection is now closed

# A new sub-container has a new lifespan for request processing
with container() as request_container:
    service = request_container.get(Service)  # a new Service instance
```

6. **Close the container** when done.

```python
container.close()
```

<details>
<summary>Full example:</summary>

```python
import sqlite3
from collections.abc import Iterable
from sqlite3 import Connection
from typing import Protocol

from dishka import Provider, Scope, make_container, provide


class APIClient:
    ...


class UserDAO(Protocol):
    ...


class SQLiteUserDAO(UserDAO):
    def __init__(self, connection: Connection):
        ...


class Service:
    def __init__(self, client: APIClient, user_dao: UserDAO):
        ...


service_provider = Provider(scope=Scope.REQUEST)
service_provider.provide(Service)
service_provider.provide(SQLiteUserDAO, provides=UserDAO)
service_provider.provide(APIClient, scope=Scope.APP)  # override provider's scope


class ConnectionProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def new_connection(self) -> Iterable[Connection]:
        connection = sqlite3.connect(":memory:")
        yield connection
        connection.close()


container = make_container(service_provider, ConnectionProvider())

# APIClient is bound to Scope.APP, so it can be accessed here
# or from any scope inside including Scope.REQUEST
client = container.get(APIClient)
client = container.get(APIClient)  # the same APIClient instance as above

# A sub-container to access shorter-living objects
with container() as request_container:
    # Service, UserDAO implementation, and Connection are bound to Scope.REQUEST,
    # so they are accessible here. APIClient can also be accessed here
    service = request_container.get(Service)
    service = request_container.get(Service)  # the same Service instance as above

# Since we exited the context manager, the sqlite3 connection is now closed

# A new sub-container has a new lifespan for request processing
with container() as request_container:
    service = request_container.get(Service)  # a new Service instance

container.close()
```
</details>

7. **(optional) Integrate with your framework.** If you are using a supported framework, add decorators and middleware for it.
   For more details, see [Using with frameworks](http://localhost:63342/dishka-fork/docs-build/html/integrations/index.html).

```python
from fastapi import APIRouter, FastAPI
from dishka import make_async_container
from dishka.integrations.fastapi import (
    FastapiProvider,
    FromDishka,
    inject,
    setup_dishka,
)

app = FastAPI()
router = APIRouter()
app.include_router(router)
container = make_async_container(
    service_provider,
    ConnectionProvider(),
    FastapiProvider(),
)
setup_dishka(container, app)


@router.get("/")
@inject
async def index(service: FromDishka[Service]) -> str:
    ...
```

### Concepts

**Dependency** is what you need for some parts of your code to work.
Dependencies are simply objects you don't create directly in place and might want to replace someday, at least for
testing purposes.
Some of them live for the entire application lifetime, while others are created and destroyed with each request.
Dependencies can also rely on other objects, which then become their dependencies.

**Scope** is the lifespan of a dependency. Standard scopes are (with some skipped):

`APP` -> `REQUEST` -> `ACTION` -> `STEP`.

You decide when to enter and exit each scope, but this is done one by one.
You set a scope for each dependency when you configure how it is created.
If the same dependency is requested multiple times within a single scope without leaving it, then by default the same
instance is returned.

For a web application, enter `APP` scope on startup and `REQUEST` scope for each HTTP request.

You can create a custom scope by defining your own `Scope` class if the standard scope flow doesn't fit your needs.

**Container** is what you use to get your dependencies.
You simply call `.get(SomeType)` and it finds a way to provide you with an instance of that type.
Container itself doesn't create objects but manages their lifecycle and caches.
It delegates object creation to providers that are passed during creation.

**Provider** is a collection of functions that provide concrete objects.
`Provider` is a class with attributes and methods, each being the result of `provide`, `alias`, `from_context`, or
`decorate`.
They can be used as provider methods, functions to assign attributes, or method decorators.

`@provide` can be used as a decorator for a method.
This method will be called when the corresponding dependency has to be created.
Name doesn't matter: just make sure it's different from other `Provider` attributes.
Type hints do matter: they indicate what this method creates and what it requires.
All method parameters are treated as dependencies and are created using the container.

If `provide` is applied to a class, that class itself is treated as a factory (its `__init__` parameters are analyzed).
Remember to assign this call to an attribute; otherwise, it will be ignored.

**Component** is an isolated group of providers within the same container, identified by a unique string.
When a dependency is requested, it is only searched within the same component as its direct dependant, unless explicitly
specified otherwise.

This structure allows you to build different parts of the application separately without worrying about using the same
types.
