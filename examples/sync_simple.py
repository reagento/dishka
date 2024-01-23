from typing import Generator

from dishka import Provider, Scope, alias, make_container, provide


class BaseA:
    pass


class A(BaseA):
    def __init__(self, x: str):
        self.x = x

    def __repr__(self):
        return f"A({self.x})"


class MyProvider(Provider):
    def __init__(self, a: int):
        super().__init__()
        self.a = a

    get_a = provide(A, scope=Scope.REQUEST)
    get_basea = alias(source=A, provides=BaseA)

    @provide(scope=Scope.APP)
    def get_int(self) -> int:
        return self.a

    @provide(scope=Scope.REQUEST)
    def get_str(self, dep: int) -> Generator[None, str, None]:
        yield f">{dep}<"


def main():
    with make_container(MyProvider(1), with_lock=True) as container:
        print(container.get(int))
        with container() as c_request:
            print(c_request.get(BaseA))
        with container() as c_request:
            print(c_request.get(A))


if __name__ == '__main__':
    main()
