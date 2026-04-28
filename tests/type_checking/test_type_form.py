import sys

from dishka import (
    Provider,
    Scope,
    make_container,
)

provider = Provider(scope=Scope.APP)

if sys.version_info >= (3, 15):
    def get_union_type() -> int | str:
        return 1
    provider.provide(get_union_type)
    container = make_container(provider)
    union_type = int | str
    union_result: int | str = container.get(union_type)
else:
    def get_int() -> int:
        return 1
    provider.provide(get_int)
    container = make_container(provider)
    int_type = int
    int_result: int = container.get(int_type)
