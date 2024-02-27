from classes import *

from dishka import Provider, provide
from dishka.container import make_container


class MyProvider(Provider):
    a = provide(A1, scope=MyScope.REQUEST, provides=A)
    c1 = provide(CA, scope=MyScope.REQUEST)
    c2 = provide(CAA, scope=MyScope.REQUEST)
    c3 = provide(CAAA, scope=MyScope.REQUEST)
    c4 = provide(CAAAA, scope=MyScope.REQUEST)
    c5 = provide(CAAAAA, scope=MyScope.REQUEST)

    @provide(scope=MyScope.REQUEST)
    def make_b(self) -> B:
        return B(2)

    @provide(scope=MyScope.REQUEST)
    def make_c(self, x: CA) -> C:
        return C(x)


def main():
    container =  make_container(MyProvider(), scopes=MyScope)
    for x in range(NUMBER):
        with container() as state:
            state.get(A)


if __name__ == '__main__':
    main()
