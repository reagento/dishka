.. _rq:

rq
===========================================

Though it is not required, you can use dishka-rq integration. It features:

* automatic REQUEST and SESSION scope management using Worker subclass
* automatic injection of dependencies into job function.

How to use
****************

1. Create provider and container as usual.

.. code-block:: python

  class StrProvider(Provider):
      @provide(scope=Scope.REQUEST)
      def hello(self) -> str:
          return "Hello"

  provider = StrProvider()
  container = make_container(provider)

2. Import.

.. code-block:: python

  from dishka import FromDishka

3. Mark those of your job functions parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

  def hello_world(hello: FromDishka[str]):
      return f"{hello} world!"

4. Run you worker using your container and DishkaWorker subclass.

.. code-block:: python

  conn = Redis()
  queues = ["default"]
  worker = DishkaWorker(container=container, queues=queues, connection=conn)
  worker.work(with_scheduler=True)

.. code-block:: shell

  python run_worker.py
