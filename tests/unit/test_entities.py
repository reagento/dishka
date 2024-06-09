from typing import Annotated, Any

import pytest

from dishka.entities.key import FromComponent, hint_to_dependency_key


class TestDependencyKey:
    @pytest.mark.parametrize(
        ("hint", "component"),
        [
            (Any, None),
            (str, None),
            (Annotated[str, {"foo": "bar"}], None),
            (Annotated[str, FromComponent("baz")], "baz"),
        ],
    )
    def test_hint_to_dependency_key(self, hint: Any, component: str | None):
        key = hint_to_dependency_key(hint)
        assert key.component == component
