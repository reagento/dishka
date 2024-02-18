.. _technical-requirements:

Technical requirements
*********************************************

1. Scopes
================

1. Library should support various number of scopes
2. All dependencies are attached to scopes before any of them can be created
3. There should be default set of scopes
4. Scopes are ordered. Order is defined when declaring scopes.
5. Scope can be entered and exited.
6. Scope can be entered not earlier than enter into previous one.
7. Same scope can be entered multiple times concurrently.
8. If the same dependency is requested more than one time within the scope the same instance is returned. Cache is not shared between concurrent instances of same scope
9. Dependency can require other dependencies of the same or previous scope.

2. Concurrency
================

1. Containers should be allowed to use with multithreading or asyncio. Not required to support both within same object. 
2. Dependency creation using async functions should be supported if container is configured to run in asyncio 
3. Concurrent entrance of scopes must not break requirement of single instance of dependency. Type of concurrency model can be configured when creating container 
4. User of container may be allowed to switch synchronization on or off for performance tuning

3. Clean dependencies
========================

1. Usage of container must not require modification of objects we are creating
2. Container must not require to be global variable.
3. Container can require code changes on the borders of scopes (e.g. application start, middlewares, request handlers)

4. Lifecycle
================

1. Dependencies which require some cleanup must be cleaned up on the scope exit
2. Dependencies which do not require cleanup should somehow be supported

5. Context data
================

1. It should be allowed to pass some data when entering the scope
2. Context data must be accessible when creating dependencies

6. Modularity
================

1. There can be multiple containers within same code base for different purposes
2. There must be a way to assemble a container from some reusable parts.
3. Assembling of container should be done in runtime in local scope

7. Usability
================

1. There should be a way to create dependency based on its ``__init__``
2. When creating a dependency there should be a way to decide which subtype is used and request only its dependencies
3. There should be a way to reuse same object for multiple requested types
4. There should be a way to decorate dependency just adding new providers

8. Integration
================

1. Additional helpers should be provided for some popular frameworks. E.g: flask, fastapi, aiogram, celery, apscheduler
2. These helpers should be optional
3. Additional integrations should be done without changing library code
