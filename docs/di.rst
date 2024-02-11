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

Here, the ``client`` is a **dependency**. Imagine that you have many methods working with same client and each methods knows how to create the client. Than think about these question?

* How do they get the ``token``? Should the every method read it on its own?
* What if the ``Client`` constructor will require more than only token? Should we copy-paste new parameters to each method?
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
    client = Client(token)
    service.action(client)

 It works well unless you have many methods and they can call each other. Also we change the signature of methods, which can lead to big code changes and impossible to be done if there is an expectation about the interface of an object.

2. **Constructor injection**. We can pass client when constructing service instance. All its methods will have access to it. It is a primary way to do DI

.. code-block:: python

    class Service:
        def __init__(self, client: Client):
            self.client = client

        def action(self):
            self.client.get_data()

    client = Client(token)
    service = Service(client)
    service.action()

3. **Attribute injection**. We can store an attribute directly (or using additional methods) on the constructed object. It mostly used in combination with constructor injection to change existing objects, or to break cycle references between objects.

.. code-block:: python

    class Service:
        def action(self):
            self.client.get_data()

    service = Service(client)
    service.client = Client(token)
    service.action()


Additionally I need to name antipatterns, which should be avoided as they cannot solve all the problems which are elimintated by DI, though they can solve part of them:

* *Global variable*. Though it allows us to reuse a dependency and configure it outside of our business logic we are limited to one instance forever. Also, we do not control when it is created and finalized: some code can try to use it before it is properly configured

* *Singleton*. It's mostly a variant of global variable. It can add laziness, but other characteristics are the same.

* *Monkey patch*. Or `mock.patch()` as an example. It allows to replace behavior in tests but it also relies on details how the class is imported and used instead of its interface. That make tests more fragile and requires more work to support them

When to inject dependencies?
===================================

It is a good idea to divide the code which uses dependencies and the code which creates them. Usually we want to reduce the knowledge about our dependencies in the code which uses them. But it is not always possible.

Different objects have different lifespan. For example, configuration is usually loaded during application startup, but database transactions should be opened separately for each processing HTTP-request. So it is unavoidable to create and finalize dependencies somewhere inside request processing. Other dependencies will have their own **scopes**, but often there are only two of them: the application lifetime and each request.

For web application it can look like this:

.. code-block:: python

    @app.get("/")
    def index(request):
        service.action()

The trick is how to manager those dependencies when you have a lot of request handlers without losing ability to test them.

* On approach is to create all those dependencies in middleware (it's a special object which is called by your framework on each event).In pseudo-code it will be kind of this:

.. code-block:: python

    def service_creator(request):
        request.state.service = Service(client)
        request.state.service.client = Client(token)

    app.setup_middleware(service_creator)

    @app.get("/")
    def index(request):
        service = request.state.service
        service.action()

It works good. You have clean request handlers and you can change middlewares in tests. But it can become a problem if you have lot's of objects which are not cheap to create.

* The second approach is to create some factory (let's call it **container**) and call it within request handler. You can still use middleware to pass it into handler (check also others features of your framework)

.. code-block:: python

    container = Container()
    def container_middleware(request):
        request.state.container = container

    app.setup_middleware(container_middleware)

    @app.get("/")
    def index(request):
        service = container.get_service()
        service.action()

Comparing to middleware it allows you to create only needed objects. But beware of accessing a container from handlers via global variable - that will make tests more difficult to maintain.
