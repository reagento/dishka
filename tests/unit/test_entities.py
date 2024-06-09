from typing import Annotated, Any

import pytest

from dishka.entities.key import FromComponent, hint_to_dependency_key


class TestDependencyKey:
    @pytest.mark.parametrize(
        ("hint", "resolved_type", "component"),
        [
            (Any, Any, None),
            (str, str, None),
            (Annotated[str, {"foo": "bar"}], str, None),
            (Annotated[str, FromComponent("baz")], str, "baz"),
            (Annotated[str, FromComponent("baz")], str, "baz"),
        ],
    )
    def test_hint_to_dependency_key(
        self,
        hint: Any,
        resolved_type: Any,
        component: str | None,
    ):
        key = hint_to_dependency_key(hint)
        assert key.type_hint == resolved_type
        assert key.component == component
