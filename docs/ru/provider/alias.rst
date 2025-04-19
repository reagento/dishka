.. _ru-alias:

alias
****************

``alias`` используется для того, чтобы можно было получать один и тот же объект по разным type hints. Например, вы настроили предоставление объекта ``A`` и хотите использовать его как AProtocol: ``container.get(A) == container.get(AProtocol)``.

Объект Provider также имеет метод ``.alias`` с такой же логикой.

.. code-block:: python

    from dishka import alias, provide, Provider, Scope

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> A:
            return A()

        a_proto = alias(source=A, provides=AProtocol)

Кроме того, у алиаса есть собственная настройка кеширования: по умолчанию он кешируется, независимо от того, кешируется ли источник. Вы можете отключить это, указав аргумент ``cache=False``.

Хотите переопределить алиас? Для этого укажите параметр ``override=True``. Это можно проверить при передаче соответствующих ``validation_settings`` при создании контейнера.

.. code-block:: python

    from dishka import provide, Provider, Scope, alias, make_container

    class MyProvider(Provider):
        scope=Scope.APP
        get_int = provide(int)
        get_float = provide(float)

        a_alias = alias(int, provides=complex)
        a_alias_override = alias(float, provides=complex, override=True)

    container = make_container(MyProvider())
    a = container.get(complex)  # 0.0
