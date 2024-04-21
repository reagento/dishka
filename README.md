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

This library is targeting to provide only an IoC-container but make it really useful. If you are tired manually passing objects to create others objects which are only used to create more objects - we have a solution. Not all project require an IoC-container, but check what we have.

Unlike other instruments we are not trying to solve tasks not related to dependency injection. We want to keep DI in place, not soiling you code with global variables and additional specifiers in all places.

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

2. Create `Provider` instance. It is only used to setup all factories providing your objects.

```python
from dishka import Provider

provider = Provider()
```

3. Register functions which provide dependencies. Do not forget to place correct typehints for parameters and result. We use `scope=Scope.APP` for dependencies which ar created only once in applicaiton lifetime, and `scope=Scope.REQUEST` for those which should be recreated for each processing request/event/etc.

```python
from dishka import Provider, Scope

def get_a() -> A:
   return A()

def get_b(a: A) -> B:
   return B(a)

provider = Provider()
provider.provide(get_a, scope=Scope.APP)
provider.provide(get_b, scope=Scope.REQUEST)
```

This can be also rewritten using classes:

```python
from dishka import provide, Provider, Scope

class MyProvider(Provider):
  @provide(scope=Scope.APP)
  def get_a(self) -> A:
     return A()
  
  @provide(scope=Scope.REQUEST)
  def get_b(self, a: A) -> B:
     return B(a)

provider = MyProvider()
```

4. Create Container instance passing providers, and step into `APP` scope. Container holds dependencies cache and is used to retrieve them. Here, you can use `.get` method to access APP-scoped dependencies:

```python
from dishka import make_container
container = make_container(provider)  # it has Scope.APP
a = container.get(A)  # `A` has Scope.APP, so it is accessible here
```

5. You can enter and exit `REQUEST` scope multiple times after that:

```python
from dishka import make_container
container = make_container(provider)
with container() as request_container:
    b = request_container.get(B)  # `B` has Scope.REQUEST
    a = request_container.get(A)  # `A` is accessible here too

with container() as request_container:
    b = request_container.get(B)  # another instance of `B`
    a = request_container.get(A)  # the same instance of `A`
```

6. Close container in the end:

```python
container.close()
```

7. If you are using supported framework add decorators and middleware for it.

```python
from dishka.integrations.fastapi import (
    FromDishka, inject, setup_dishka,
)

@router.get("/")
@inject
async def index(a: FromDishka[A]) -> str:
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

If `provide` is used with some class then that class itself is treated as a factory (`__init__` is analyzed for parameters). But do not forget to assing that call to some attribute otherwise it will be ignored.

**Component** - is an isolated group of providers within the same container identified by a string. When dependency is requested it is searched only within the same component as its dependant, unless it is declared explicitly.

This allows you to have multiple parts of application build separately without need to think if the use same types.

### Tips

* Add method and mark it with `@provide` decorator. It can be sync or async method returning some value.

    ```python
    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> A:
            return A()
    ```
* Want some finalization when exiting the scope? Make that method generator:

    ```python
    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> Iterable[A]:
            a = A()
            yield a
            a.close()
    ```
* Do not have any specific logic and just want to create class using its `__init__`? then add a provider attribute using `provide` as function passing that class. 

    ```python 
    class MyProvider(Provider):
        a = provide(A, scope=Scope.REQUEST)
    ```
* Want to create a child class instance when parent is requested? add a `source` attribute to `provide` function with a parent class while passing child as a first parameter

    ```python 
    class MyProvider(Provider):
        a = provide(source=AChild, scope=Scope.REQUEST, provides=A)
    ```
* Having multiple interfaces which can be created as a same class? Use `AnyOf`:

    ```python
    from dishka import AnyOf

    class MyProvider(Provider):
        @provide
        def p(self) -> AnyOf[A, AProtocol]:
            return A()
    ```

    Use alias if you want to add them in another `Provider`:

    ```python
    class MyProvider2(Provider):
        p = alias(source=A, provides=AProtocol)
    ```

    In both cases it works the same way as

    ```python
    class MyProvider2(Provider):
        @provide(scope=<Scope of A>)
        def p(self, a: A) -> AProtocol:
            return a
    ```


* Want to apply decorator pattern and do not want to alter existing provide method? Use `decorate`. It will construct object using earlie defined provider and then pass it to your decorator before returning from the container.

  ```python
    class MyProvider(Provider):
        @decorate
        def decorate_a(self, a: A) -> A:
            return ADecorator(a)
   ```
  Decorator function can also have additional parameters.

* Want to go `async`? Make provide methods asynchronous. Create async container. Use `async with` and await `get` calls:

```python
class MyProvider(Provider):
   @provide(scope=Scope.APP)
   async def get_a(self) -> A:
      return A()

container = make_async_container(MyProvider())
a = await container.get(A)
```

* Having some data connected with scope which you want to use when solving dependencies? Set it when entering scope. These classes can be used as parameters of your `provide` methods. But you need to specify them in provider as retrieved form context.

```python
from dishka import from_context, Provider, provide, Scope

class MyProvider(Provider):
    scope = Scope.REQUEST

    app = from_context(provides=App, scope=Scope.APP)
    request = from_context(provides=RequestClass)

    @provide
    def get_a(self, request: RequestClass, app: App) -> A:
        ...

container = make_container(MyProvider(), context={App: app})
with container(context={RequestClass: request_instance}) as request_container:
    pass
```

* Having to many dependencies? Or maybe want to replace only part of them in tests keeping others? Create multiple `Provider` classes

```python
container = make_container(MyProvider(), OtherProvider())
```

* Tired of providing `scope==` for each depedency? Set it inside your `Provider` class and all dependencies with no scope will use it.

```python
class MyProvider(Provider):
   scope = Scope.APP

   @provide
   async def get_a(self) -> A:
      return A()
```
