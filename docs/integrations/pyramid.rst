.. _pyramid:


Pyramid
===========================================

How to use
****************


1. Import


..  code-block:: python


    from dishka.integrations.pyramid import (
        PyramidProvider,
        inject,
        setup_dishka,
    )
    from dishka import FromDishka, make_container, Provider, provide, Scope


2. Create provider. You can use ``pyramid.request.Request`` as a factory parameter to access HTTP request.
It is available on *REQUEST*-scope


.. code-block:: python


    from pyramid.request import Request

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
            ...


3. Mark those of your view parameters which are to be injected with ``FromDishka[]`` and decorate them using ``@inject``


.. code-block:: python


    @view_config(route_name='home')
    @inject
    def my_view(
        request,
        gateway: FromDishka[Gateway],
    ):
        ...


4. Use ``PyramidProvider()`` when creating container if you are going to use ``pyramid.request.Request`` in providers


.. code-block:: python


    container = make_container(YourProvider(), PyramidProvider())


5. Setup ``dishka`` integration using ``Configurator``. It is important to call it before calling ``config.make_wsgi_app()``


.. code-block:: python


    from pyramid.config import Configurator

    config = Configurator()
    config.add_route('home', '/')
    config.add_view(my_view, route_name='home')

    container = make_container(YourProvider(), PyramidProvider())
    setup_dishka(container, config)

    app = config.make_wsgi_app()


**Note:** Container is automatically closed when Pyramid application shuts down.


Full example
****************


.. code-block:: python


    from pyramid.config import Configurator
    from pyramid.request import Request
    from pyramid.response import Response

    from dishka import FromDishka, make_container, Provider, provide, Scope
    from dishka.integrations.pyramid import (
        PyramidProvider,
        inject,
        setup_dishka,
    )


    class Gateway:
        def get_data(self) -> str:
            return "Hello from Gateway"


    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_gateway(self, request: Request) -> Gateway:
            return Gateway()


    @inject
    def my_view(
        request,
        gateway: FromDishka[Gateway],
    ) -> Response:
        data = gateway.get_data()
        return Response(data)


    def main():
        config = Configurator()
        config.add_route('home', '/')
        config.add_view(my_view, route_name='home')

        container = make_container(YourProvider(), PyramidProvider())
        setup_dishka(container, config)

        return config.make_wsgi_app()


    if __name__ == '__main__':
        from waitress import serve
        app = main()
        serve(app, host='0.0.0.0', port=4000)
