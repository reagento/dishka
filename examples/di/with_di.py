from di import Container, bind_by_type
from di.dependent import Dependent
from di.executors import SyncExecutor

from classes import *


def make_b():
    return B(2)


def make_c():
    return C(1)


def main():
    container = Container()
    container.bind(bind_by_type(Dependent(A1, scope=MyScope.REQUEST), A))
    container.bind(bind_by_type(Dependent(CA, scope=MyScope.REQUEST), CA))
    container.bind(bind_by_type(Dependent(CAA, scope=MyScope.REQUEST), CAA, ))
    container.bind(bind_by_type(Dependent(CAAA, scope=MyScope.REQUEST), CAAA))
    container.bind(bind_by_type(Dependent(CAAAA, scope=MyScope.REQUEST), CAAAA))
    container.bind(bind_by_type(Dependent(CAAAA, scope=MyScope.REQUEST), CAAAA))
    container.bind(bind_by_type(Dependent(make_b, scope=MyScope.REQUEST), B))
    container.bind(bind_by_type(Dependent(make_c, scope=MyScope.REQUEST), C))

    executor = SyncExecutor()
    solved = container.solve(Dependent(A, scope=MyScope.REQUEST), scopes=list(MyScope))
    with container.enter_scope(MyScope.APP) as app_state:
        for x in range(NUMBER):
            with app_state.enter_scope(MyScope.REQUEST) as state:
                solved.execute_sync(executor=executor, state=state)

if __name__ == '__main__':
    main()
