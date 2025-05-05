.. _provide_all:

provide_all
******************

``provide_all`` is a helper function which can be used instead of repeating ``provide`` call with just class passed and same scope.

These two providers are equal for the container:

.. code-block:: python

    from dishka import provide, provide_all, Provider, Scope

    class OneByOne(Provider):
        scope = Scope.APP

        register_user = provide(RegisterUserInteractor)
        update_pfp = provide(UpdateProfilePicInteractor)

    class AllAtOnce(Provider):
        scope = Scope.APP

        interactors = provide_all(
            RegisterUserInteractor,
            UpdateProfilePicInteractor
        )


It is also available as a method:

.. code-block:: python

    provider = Provider(scope=Scope.APP)
    provider.provide_all(
        RegisterUserInteractor,
        UpdateProfilePicInteractor
    )


You can combine different ``provide``, ``alias``, ``decorate``, ``from_context``, ``provide_all``, ``from_context`` and others with each other without thinking about the variable names for each of them.

These two providers are equal for the container:

.. code-block:: python

    from dishka import alias, decorate, provide, provide_all, Provider, Scope

    class OneByOne(Provider):
        scope = Scope.APP

        config = from_context(Config)
        user_dao = provide(UserDAOImpl, provides=UserDAO)
        post_dao = provide(PostDAOImpl, provides=PostDAO)
        post_reader = alias(source=PostDAOImpl, provides=PostReader)
        decorator = decorate(SomeDecorator, provides=SomeClass)

    class AllAtOnce(Provider):
        scope = Scope.APP

        provides = (
            provide(UserDAOImpl, provides=UserDAO)
            + provide(PostDAOImpl, provides=PostDAO)
            + alias(source=PostDAOImpl, provides=PostReader)
            + decorate(SomeDecorator, provides=SomeClass)
            + from_context(Config)
        )
