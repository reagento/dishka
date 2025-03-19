import sys
from typing import Any

import pytest

from dishka import Provider, Scope, make_container, provide

if sys.version_info >= (3, 12):
    type Integer = int
    type Integer2 = int
    type ListFloat = list[float]
    type DictIntStr = dict[int, str]


    class MainProvider(Provider):
        @provide(scope=Scope.APP)
        def get_integer(self) -> Integer:
            return 1

        @provide(scope=Scope.APP)
        def get_list_float(self) -> ListFloat:
            return [1.1, 1.2]

        @provide(scope=Scope.APP)
        def get_dict_int_str(self) -> DictIntStr:
            return {1: "1"}


class TestTypeAliasType:
    @pytest.mark.parametrize(
        ("hint", "resolved_type"),
        [
            (int, 1),
            (Integer2, 1),
            (list[float], [1.1, 1.2]),
            (dict[int, str], {1: "1"}),
        ],
    )
    def test_type_alias_type(
            self,
            hint: Any,
            resolved_type: Any,
    ):
        if sys.version_info >= (3, 12):
            container = make_container(MainProvider())
            assert container.get(hint) == resolved_type
        else:
            pytest.skip("Unsupported Python version")
