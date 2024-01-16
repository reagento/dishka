from contextlib import contextmanager
from enum import auto

from dishka import provide, Scope, Provider, Container


class MyScope(Scope):
    APP = auto()
    REQUEST = auto()


class MyProvider(Provider):
    def __init__(self, a: int):
        self.a = a

    @provide(MyScope.APP)
    @contextmanager
    def get_int(self) -> int:
        print("solve int")
        yield self.a

    @provide(MyScope.REQUEST)
    @contextmanager
    def get_str(self, dep: int) -> str:
        print("solve str")
        yield f">{dep}<"


def main():
    container = Container(
        MyProvider(1), scope=MyScope.APP, with_lock=True,
    )
    print(container.get(int))

    with container() as c_request:
        print(c_request.get(str))

    with container() as c_request:
        print(c_request.get(str))
    container.close()


if __name__ == '__main__':
    main()
