import sys
from typing import Any

import pytest

from dishka import Provider, Scope, make_container, provide

if sys.version_info >= (3, 12):

    from .type_alias_type_provider import (
        DictIntStr,
        Integer,
        Integer2,
        ListFloat,
        WrappedInteger,
    )

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

        @provide(scope=Scope.APP)
        def get_wrapped_integer(self) -> WrappedInteger:
            return 1


    class TestTypeAliasType:
        @pytest.mark.parametrize(
            ("hint", "resolved_type"),
            [
                (int, 1),
                (Integer2, 1),
                (list[float], [1.1, 1.2]),
                (dict[int, str], {1: "1"}),
                (WrappedInteger, 1),
            ],
        )
        def test_type_alias_type(
                self,
                hint: Any,
                resolved_type: Any,
        ):
            container = make_container(MainProvider())
            assert container.get(hint) == resolved_type

else:
    class TestTypeAliasType:
        @pytest.mark.skip("Unsupported Python version")
        def test_type_alias_type(self):
            ...
