from enum import auto
from typing import Iterable, Generator

from dishka import provide, Scope, Provider, make_container


class MyScope(Scope):
    APP = auto()
    REQUEST = auto()


class MyProvider(Provider):
    def __init__(self, a: int):
        super().__init__()
        self.a = a

    @provide(scope=MyScope.APP)
    def get_int(self) -> Iterable[int]:
        print("solve int")
        yield self.a

    @provide(scope=MyScope.REQUEST)
    def get_str(self, dep: int) -> Generator[None, str, None]:
        print("solve str")
        yield f">{dep}<"


def main():
    container = make_container(
        MyProvider(1), scopes=MyScope, with_lock=True,
    )
    print(container.get(int))

    with container() as c_request:
        print(c_request.get(str))

    with container() as c_request:
        print(c_request.get(str))
    container.close()


if __name__ == '__main__':
    main()
