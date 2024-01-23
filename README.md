## DIshka (from russian "small DI")

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

### Quickstart

1. Create Provider subclass. 
2. Mark methods which actually create depedencies with `@provide` decorator with carefully arranged scopes.
3. Do not forget to place correct typehints for parameters and result 
4. Create Container instance passing providers
5. Call `get` to get dependency and use context manager to get deeper through scopes
6. Add decorators and middleware for your framework

See [examples](examples/sync_simple.py)

### Concepts

**Dependency** is what you need for some part of your code to work. They are just object which you do not create in place and probably want to replace some day. At least for tests.
Some of them can live while you application is running, others are destroyed and created on each request. Dependencies can depend on other objects, which are their dependencies.

**Scope** is a lifespan of a dependency. Standard scopes are `APP` -> `REQUEST` -> `ACTION` -> `STEP`. You manage when to enter and exit them, but it is done one by one. You set a scope for your dependency when you configure how to create it. If the same dependency is requested multiple time within one scope without leaving it, then the same instance is returned. 

**Container** is what you use to get your dependency. You just call `.get(SomeType)` and it finds a way to get you an instance of that type. It does not create things itself, but manages their lifecycle and caches.
```python
# create container and enter APP scope
with make_container(provider) as container:
    # here you can get APP-scoped dependencies
    container.get(SomeType)
    
    # enter the next scope which is REQUEST
    with container() as request_container:
        # here you can get REQUEST-scoped dependencies or APP-scoped ones
        request_container.get(OtherType)
        
    # you can pass existing objects when entering scope
    # they can be retrieved using `get` or used when resolving dependencies
    with container({RequestClass: request_instance}) as request_container:
        pass
```


**Provider** is a collection of functions which really provide some objects. 
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