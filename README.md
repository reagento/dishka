## Dishka (from russian "cute DI")

[![PyPI version](https://badge.fury.io/py/dishka.svg)](https://pypi.python.org/pypi/dishka)
[![Supported versions](https://img.shields.io/pypi/pyversions/dishka.svg)](https://pypi.python.org/pypi/dishka)
[![downloads](https://img.shields.io/pypi/dm/dishka.svg)](https://pypistats.org/packages/dishka)
[![license](https://img.shields.io/github/license/reagento/dishka)](https://github.com/reagento/dishka/blob/master/LICENSE)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/reagento/dishka/setup.yml)](https://github.com/reagento/dishka/actions)
[![Doc](https://readthedocs.org/projects/dishka/badge/?version=latest&style=flat)](https://dishka.readthedocs.io)
[![Telegram](https://img.shields.io/badge/💬-Telegram-blue)](https://t.me/reagento_ru)

Cute DI framework with scopes and agreeable API.

📚 [Documentation](https://dishka.readthedocs.io)

### Purpose

This library is targeting to provide only an IoC-container but tries to make it really useful. 
If you are tired manually passing objects to create others objects which are only used to create more objects - we have a solution. 
Not all project require an IoC-container, but check what we have.

Unlike other instruments we are not trying to solve tasks not related to [dependency injection](https://dishka.readthedocs.io/en/latest/di_intro.html). We want to keep DI in place, not soiling you code with global variables and additional specifiers in all places.

Main ideas:
* **Scopes**. Any object can have lifespan of the whole app, single request or even more fractionally. Many frameworks do not have scopes or have only 2 of them. Here you can have as many scopes as you need.
* **Finalization**. Some dependencies like database connections must be not only created, but carefully released. Many framework lack this essential feature
* **Modular providers**. Instead of creating lots of separate functions or contrariwise a big single class, you can split your factories into several classes, which makes them simpler reusable.
* **Clean dependencies**. You do not need to add custom markers to the code of dependencies so to allow library to see them. All customization is done within providers code and only borders of scopes have to deal with library API.
* **Simple API**. You need minimum of objects to start using library. You can easily integrate it with your task framework, examples provided.
* **Speed**. It is fast enough so you not to worry about. It is even faster than many of the analogs.

See more in [technical requirements](https://dishka.readthedocs.io/en/latest/requirements/technical.html)

### Quickstart

1. Install dishka

```shell
pip install dishka
```

2. Write your classes, fill type hints. Imagine, you have two classes: Service (kind of business logic) and DAO (kind of data access) and some external api client:

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

4. Create Provider instance. It is only used to setup all factories providing your objects.

```python
from dishka import Provider

provider = Provider()
```


5. Setup how to provide dependencies.

We use `scope=Scope.APP` for dependencies which are created only once in application lifetime,
and `scope=Scope.REQUEST` for those which should be recreated for each processing request/event/etc.
To read more about scopes, refer [documentation](https://dishka.readthedocs.io/en/latest/advanced/scopes.html)

```python
from dishka import Provider, Scope

service_provider = Provider(scope=Scope.REQUEST)
service_provider.provide(Service)
service_provider.provide(DAOImpl, provides=DAO)
service_provider.provide(SomeClient, scope=Scope.APP)  # override provider scope
```

To provide connection we might need to write some custom code:

```python
from dishka import Provider, provide, Scope

class ConnectionProvider(Provider):
    @provide(Scope=Scope.REQUEST)
    def new_connection(self) -> Connection:
        conn = sqlite3.connect()
        yield conn
        conn.close()
```

6. Create main `Container` instance passing providers, and step into `APP` scope.

```python
from dishka import make_container

container = make_container(service_provider, ConnectionProvider())
```

7. Container holds dependencies cache and is used to retrieve them. Here, you can use `.get` method to access APP-scoped dependencies:

```python
client = container.get(SomeClient)  # `SomeClient` has Scope.APP, so it is accessible here
client = container.get(SomeClient)  # same instance of `SomeClient`
```


8. You can enter and exit `REQUEST` scope multiple times after that using context manager:

```python
# subcontainer to access more short-living objects
with container() as request_container:
    service = request_container.get(Service)
    service = request_container.get(Service)  # same service instance
# at this point connection will be closed as we exited context manager

# new subcontainer to have a new lifespan for request processing
with container() as request_container:
    service = request_container.get(Service)  # new service instance
```


9. Close container in the end:

```python
container.close()
```

10. If you are using supported framework add decorators and middleware for it.
For more details see [integrations doc](https://dishka.readthedocs.io/en/latest/integrations/index.html)

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

**Dependency** is what you need for some part of your code to work. They are just object which you do not create in place and probably want to replace some day. At least for tests.
Some of them can live while you application is running, others are destroyed and created on each request. Dependencies can depend on other objects, which are their dependencies.

**Scope** is a lifespan of a dependency. Standard scopes are (without skipped ones):

  `APP` -> `REQUEST` -> `ACTION` -> `STEP`.

You decide when to enter and exit them, but it is done one by one. You set a scope for your dependency when you configure how to create it. If the same dependency is requested multiple time within one scope without leaving it, then by default the same instance is returned.

If you are developing web application, you would enter `APP` scope on startup, and you would `REQUEST` scope in each HTTP-request.

You can provide your own Scopes class if you are not satisfied with standard flow.

**Container** is what you use to get your dependency. You just call `.get(SomeType)` and it finds a way to get you an instance of that type. It does not create things itself, but manages their lifecycle and caches. It delegates objects creation to providers which are passed during creation.

**Provider** is a collection of functions which really provide some objects. 
Provider itself is a class with some attributes and methods. Each of them is either result of `provide`, `alias` or `decorate`. They can be used as provider methods, functions to assign attributes or method decorators.

`@provide` can be used as a decorator for some method. This method will be called when corresponding dependency has to be created. Name of the method is not important: just check that it is different form other `Provider` attributes. Type hints do matter: they show what this method creates and what does it require. All method parameters are treated as other dependencies and created using container.

If `provide` is used with some class then that class itself is treated as a factory (`__init__` is analyzed for parameters). But do not forget to assign that call to some attribute otherwise it will be ignored.

**Component** - is an isolated group of providers within the same container identified by a string. When dependency is requested it is searched only within the same component as its dependant, unless it is declared explicitly.

This allows you to have multiple parts of application build separately without need to think if the use same types.
