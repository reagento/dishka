Dependency injection
*************************

What is Dependency Injection?
==================================

Dependency injection is a simple idea which says that if some object requires another object for its work it should receive it from outside instead of creating or requesting that object itself.

Imagine you have a business logic which uses some remote API client

.. code-block:: python

    class Service:
        def action(self):
            client = Client(token)
            client.get_data()

    service = Service()
    service.action()

Here, the ``client`` is a **dependency**. Imagine that you have many methods working with same client and each method knows how to create the client. Than think about these questions?

* How do they get the ``token``? Should the every method read it on its own?
* What if the ``Client`` constructor will require more than one token? Should we copy-paste new parameters to each method?
* How will we replace ``client`` with mock while testing these methods?
* How do we know which part of the code can use the ``client``?
* How can we reuse same client if it becomes stateful? How can we reuse several clients in different cases?

I hope by this moment you've started suspecting that there is a problem. To solve it let's create our **dependency** somewhere outside of this method and **inject** it.
There are three ways to do it:

1. **Parameter injection**. We can pass client to a method as a parameter.

.. code-block:: python

    class Service:
        def action(self, client: Client):
            client.get_data()

    service = Service()
    client = Client(token="1234567890")
    service.action(client)

It works well unless you have many methods and they can call each other. Also we change the signature of methods, which can lead to big code changes and impossible to be done if there is an expectation about the interface of an object.

2. **Constructor injection**. We can pass client when constructing service instance. All its methods will have access to it. It is a primary way to do DI

.. code-block:: python

    class Service:
        def __init__(self, client: Client):
            self.client = client

        def action(self):
            self.client.get_data()

    token = os.getenv("TOKEN")
    client = Client(token)
    service = Service(client)
    service.action()

3. **Attribute injection**. We can store an attribute directly (or using additional methods) on the constructed object. It is mostly used in combination with constructor injection to change existing objects, or to break cycle references between objects. E.g.

.. code-block:: python

    class Service:
        client: Client

        def action(self):
            self.client.get_data()

    service = Service(client)
    service.client = Client(token)
    service.action()

Additionally I need to name anti-patterns, which should be avoided as they cannot solve all the problems which are eliminated by DI, though they can solve part of them:

* *Global variable*. Though it allows us to reuse a dependency and configure it outside of our business logic we are limited to one instance forever. Also, we do not control when it is created and finalized: some code can try to use it before it is properly configured

* *Singleton*. It's mostly a variant of global variable. It can add laziness, but other characteristics are the same.

* *Monkey patch*. Or `mock.patch()` as an example. It allows to replace behavior in tests but it also relies on details how the class is imported and used instead of its interface. That makes tests more fragile and requires more work to support them

When to inject dependencies?
===================================

For simple cases it is obvious that you have some classes with their requirements and once you start your app you create all of them and wire together. But real applications are more complicated things. They operate dozens or even hundreds of objects in complex hierarchy, they do concurrent processing.


It is a good idea to separate the code which uses dependencies and the code which creates them. Usually we want to reduce the knowledge about our dependencies in the code which uses them. But it is not always possible as different objects have different lifespan.

For example, *configuration* is usually loaded during application startup, but *database transactions* (and corresponding *database connections*) should be opened separately for each processing HTTP-request. So it is unavoidable to create and finalize dependencies somewhere inside request processing. Other dependencies will have their own **scopes**, but often there are only two of them: the application lifetime and each request.

For web application it can look like this:

.. code-block:: python

    @app.get("/")
    def index(request):
        client = Client(os.getenv("TOKEN"))
        service = Service(client)
        service.action()

    @app.get("/foo")
    def get_foo(request):
        client = Client(os.getenv("TOKEN"))
        service = Service(client)
        service.action()

The trick is how to manage those dependencies when you have a lot of request handlers without losing ability to test them.

* One approach is to create all those dependencies in middleware (it's a special object which is called by your framework on each event). In pseudo-code it will be kind of this:

.. code-block:: python

    def service_creator(request):
        client = Client(os.getenv("TOKEN"))
        service = Service(client)
        request.state.service = Service(client)

    app.setup_middleware(service_creator)

    @app.get("/")
    def index(request):
        service = request.state.service
        service.action()

It works good. You have clean request handlers and you can change middlewares in tests. But it can become a problem if you have lot's of objects which are not cheap to create.

* The second approach is to create some factory (let's call it **container**) and call it within request handler. You can still use middleware to pass it into handler (check also other features of your framework)

.. code-block:: python

    class Container:
        def get_client(self) -> Client:
            return Client(os.getenv("TOKEN"))

        def get_service(self) -> Service:
            return Service(self.get_client())

    container = Container()
    def container_middleware(request):
        request.state.container = container

    app.setup_middleware(container_middleware)

    @app.get("/")
    def index(request):
        service = request.state.container.get_service()
        service.action()

Comparing to middleware it allows you to create only needed objects. But beware of accessing a container from handlers via global variable - that will make tests more difficult to maintain.

In both approaches you can control whether the instance is created on each request or once per app. Also you can have different middlewares or containers for production and test purposes.


What is IoC-container?
=============================

IoC-container is a special object (or a framework providing such an object) which provides required objects following dependency injection rules and manages their lifetime. DI-framework is another name for such frameworks.

Common mistake is to treat IoC-container as a single way to inject dependencies. It has nothing common with reality. Dependency injection can be done just by passing one object to another, but in complex application it is not so easy to do. As it was shown above you might want to create a separate object to encapsulate all DI-related logic. ``Container`` in previous example is an example of hand-written primitive IoC-container.

Bigger is your application, more complex factories you need, more necessary is to automate creation of a container. You do not need to use IoC-container to test one small part of application, but it can be essential for launching it in whole. Fortunately, there are frameworks for it. But again, beware of spreading container-related details around your application code with an exception on scope boundaries.

So, talking about IoC-container we can write-down these ideas:

* IoC-container is not necessary for dependency injection
* It is a useful helper for bigger applications
* It should be safe to use it in concurrent application
* It should follow the rules you provide for your dependencies (single or multiple instances, multiple lifetime scopes, etc.)

More about possible requirements you can read in :ref:`technical-requirements`.

So here is the time for **dishka** - an implementation of IoC-container with everything you need.