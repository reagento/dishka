Multiple objects of same type
============================================

By default dishka relies on approach "last wins" which means that
if you have multiple factories providing the same type
only the last of them will be used.
The same rule still applies even if factories are marked with ``when=``,
but in that case only active factories are used (see :ref:`when`)

In some cases it is useful to have all objects created instead of a single one.
To achieve that you should use ``collect`` in your provider.
By default, it provides a list of requested type.
You can use it as a dependency or request directly from a container.

.. code-block:: python

    from dishka import Provider, Scope, collect, provide, make_container


    class MyProvider(Provider):
        @provide(scope=Scope.APP)
        def handler1(self) -> Handler:
            return FirstHandler()

        @provide(scope=Scope.APP)
        def handler2(self) -> Handler:
            return SecondHandler()

        all_handlers = collect(Handler)


    c = make_container(MyProvider())
    c.get(list[Handler])   # [FirstHandler(), SecondHandler()]


It also takes ``when=`` option into account. So, only active factories will be called.

If you need, you can set a narrower scope for a collection, disable caching or change provided typehint.
Note that ``provides=`` option affects only dependency solving, a list will be created anyway

.. code-block:: python

    handlers = collect(
        Handler,
        provides=Sequence[Handler],
        scope=Scope.REQUEST,
        cache=True,
    )
