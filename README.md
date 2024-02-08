## DIshka (from russian "small DI")
[![PyPI version](https://badge.fury.io/py/dishka.svg)](https://badge.fury.io/py/dishka)
[![downloads](https://img.shields.io/pypi/dm/dishka.svg)](https://pypistats.org/packages/dishka)
[![license](https://img.shields.io/github/license/reagento/dishka)](https://github.com/reagento/dishka/blob/master/LICENSE)
[![license](https://img.shields.io/badge/💬-Telegram-blue)](https://t.me/reagento_ru)

Small DI framework with scopes and agreeable API.

### Purpose

This library is targeting to provide only an IoC-container. If you are tired manually passing objects to create others objects which are only used to create more object - we have a solution. Otherwise, you do not probably need a IoC-container but check what we have.

Unlike other instruments we are not trying to solve tasks not related to dependency injection. We want to keep DI in place, not soiling you code with global variables and additional specifiers in all places. 

Main ideas:
* **Scopes**. Any object can have lifespan of the whole app, single request or even more fractionally. Many frameworks do not have scopes or have only 2 of them. Here you can have as many scopes as you need.
* **Finalization**. Some dependencies like database connections must be not only created, but carefully released. Many framework lack this essential feature
* **Modular providers**. Instead of creating lots of separate functions or contrariwise a big single class, you can split your factories into several classes, which makes them simpler reusable.
* **Clean dependencies**. You do not need to add custom markers to the code of dependencies so to allow library to see them. All customization is done within providers code and only borders of scopes have to deal with library API.
* **Simple API**. You need minimum of objects to start using library. You can easily integrate it with your task framework, examples provided. 
* **Speed**. It is fast enough so you not to worry about. It is even faster than many of the analogs.

See more in [technical requirements](docs/technical_requirements.md)

### Quickstart

1. Create Provider subclass. 
```python
from dishka import Provider
class MyProvider(Provider):
   ...
```
2. Mark methods which actually create dependencies with `@provide` decorator with carefully arranged scopes. Do not forget to place correct typehints for parameters and result.
Here we describe how to create instances of A and B classes, where B class requires itself an instance of A.
```python
from dishka import provide, Provider, Scope
class MyProvider(Provider):
   @provide(scope=Scope.APP)
   def get_a(self) -> A:
      return A()

   @provide(scope=Scope.REQUEST)
   def get_b(self, a: A) -> B:
      return B(a)
```
4. Create Container instance passing providers, and step into `APP` scope. Or deeper if you need.
```python
with make_container(MyProvider()) as container:  # enter Scope.APP
     with container() as request_container:   # enter Scope.REQUEST
          ...
```

5. Call `get` to get dependency and use context manager to get deeper through scopes
```python
with make_container(MyProvider()) as container:
     a = container.get(A)  # `A` has Scope.APP, so it is accessible here
     with container() as request_container:
          b = request_container.get(B)  # `B` has Scope.REQUEST
          a = request_container.get(A)  # `A` is accessible here too
```

6. Add decorators and middleware for your framework (_would be described soon_)

See [examples](examples)

### Concepts

**Dependency** is what you need for some part of your code to work. They are just object which you do not create in place and probably want to replace some day. At least for tests.
Some of them can live while you application is running, others are destroyed and created on each request. Dependencies can depend on other objects, which are their dependencies.

**Scope** is a lifespan of a dependency. Standard scopes are:

  `APP` -> `REQUEST` -> `ACTION` -> `STEP`.

You decide when to enter and exit them, but it is done one by one. You set a scope for your dependency when you configure how to create it. If the same dependency is requested multiple time within one scope without leaving it, then the same instance is returned.

If you are developing web application, you would enter `APP` scope on startup, and you would `REQUEST` scope in each HTTP-request.

You can provide your own Scopes class if you are not satisfied with standard flow.

**Container** is what you use to get your dependency. You just call `.get(SomeType)` and it finds a way to get you an instance of that type. It does not create things itself, but manages their lifecycle and caches. It delegates objects creation to providers which are passed during creation.


**Provider** is a collection of functions which really provide some objects. 
Provider itself is a class with some attributes and methods. Each of them is either result of `provide`, `alias` or `decorate`.

`@provide` can be used as a decorator for some method. This method will be called when corresponding dependency has to be created. Name of the method is not important: just check that it is different form other `Provider` attributes. Type hints do matter: they show what this method creates and what does it require. All method parameters are treated as other dependencies and created using container.

If `provide` is used with some class then that class itself is treated as a factory (`__init__` is analyzed for parameters). But do not forget to assing that call to some attribute otherwise it will be ignored.



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
* Want to create a child class instance when parent is requested? add a `dependency` attribute to `provide` function with a parent class while passing child as a first parameter 
    ```python 
    class MyProvider(Provider):
        a = provide(source=AChild, scope=Scope.REQUEST, provides=A)
    ```
* Having multiple interfaces which can be created as a same class with defined provider? Use alias:
    ```python
    class MyProvider(Provider):
        p = alias(source=A, provides=AProtocol)
    ```
    it works the same way as
    ```python
    class MyProvider(Provider):
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

async with make_async_container(MyProvider()) as container:
     a = await container.get(A)
```

* Having some data connected with scope which you want to use when solving dependencies? Set it when entering scope. These classes can be used as parameters of your `provide` methods
```python
with make_container(MyProvider(), context={App: app}) as container:
    with container(context={RequestClass: request_instance}) as request_container:
        pass
```

* Having to many dependencies? Or maybe want to replace only part of them in tests keeping others? Create multiple `Provider` classes
```python
with make_container(MyProvider(), OtherProvider()) as container:
```
