import pytest

from dishka import DEFAULT_COMPONENT, DependencyKey
from dishka.context_proxy import ContextProxy


def test_simple():
    int_key = DependencyKey(int, DEFAULT_COMPONENT)
    context = {int_key: 1}
    cache = {**context, DependencyKey(float, DEFAULT_COMPONENT): 2}
    proxy = ContextProxy(context=context, cache=cache)
    assert len(proxy) == 2
    assert proxy[int_key] == proxy.get(int_key) == 1
    assert list(proxy) == list(cache)

    complex_key = DependencyKey(complex, DEFAULT_COMPONENT)
    proxy[complex_key] = 3
    assert context[complex_key] == cache[complex_key] == 3

    with pytest.raises(RuntimeError):
        del proxy[complex_key]
