import asyncio
from collections.abc import AsyncIterator
from unittest.mock import Mock

import pytest

from dishka import (
    Provider,
    Scope,
    make_async_container,
    provide,
)

# --- Helpers ---


async def _timed_get(container, key):
    """Get a dependency and return (result, elapsed_seconds)."""
    loop = asyncio.get_running_loop()
    start = loop.time()
    result = await container.get(key)
    return result, loop.time() - start


def _assert_fast(elapsed, threshold, label="deps should be gathered"):
    assert elapsed < threshold, (
        f"Took {elapsed:.3f}s, expected < {threshold}s ({label})"
    )


# --- Diamond helper mixin ---
# Many tests need the same float→int, str→int, bytes→(float,str) diamond.


class DiamondConsumersMixin:
    """Provides float(int), str(int), bytes(float, str) diamond consumers."""

    @provide(scope=Scope.APP)
    async def get_float(self, v: int) -> float:
        return float(v)

    @provide(scope=Scope.APP)
    async def get_str(self, v: int) -> str:
        return str(v)

    @provide(scope=Scope.APP)
    async def get_bytes(self, a: float, b: str) -> bytes:
        return f"{a}-{b}".encode()


# --- Basic gathering tests ---


class IndependentDepsProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.1)
        return 1

    @provide(scope=Scope.APP)
    async def get_float(self) -> float:
        await asyncio.sleep(0.1)
        return 2.0

    @provide(scope=Scope.APP)
    async def get_str(self, a: int, b: float) -> str:
        return f"{a}-{b}"


@pytest.mark.asyncio
async def test_independent_deps_gathered():
    container = make_async_container(IndependentDepsProvider())
    result, elapsed = await _timed_get(container, str)
    assert result == "1-2.0"
    # With gathering: ~0.1s. Without: ~0.2s. Use 0.15 as threshold.
    _assert_fast(elapsed, 0.15)
    await container.close()


class SharedTransitiveDepsProvider(DiamondConsumersMixin, Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.05)
        return 42


@pytest.mark.asyncio
async def test_shared_transitive_deps_gathered():
    """Shared cached transitive deps are gathered via pending sentinel."""
    container = make_async_container(SharedTransitiveDepsProvider())
    result = await container.get(bytes)
    assert result == b"42.0-42"
    await container.close()


class ThreeIndependentProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.1)
        return 1

    @provide(scope=Scope.APP)
    async def get_float(self) -> float:
        await asyncio.sleep(0.1)
        return 2.0

    @provide(scope=Scope.APP)
    async def get_bytes(self) -> bytes:
        await asyncio.sleep(0.1)
        return b"3"

    @provide(scope=Scope.APP)
    async def get_str(self, a: int, b: float, c: bytes) -> str:
        return f"{a}-{b}-{c!r}"


@pytest.mark.asyncio
async def test_three_independent_deps_gathered():
    container = make_async_container(ThreeIndependentProvider())
    result, elapsed = await _timed_get(container, str)
    assert result == "1-2.0-b'3'"
    # With gathering: ~0.1s. Without: ~0.3s.
    _assert_fast(elapsed, 0.15)
    await container.close()


class MixedSyncAsyncProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.1)
        return 1

    @provide(scope=Scope.APP)
    async def get_float(self) -> float:
        await asyncio.sleep(0.1)
        return 2.0

    @provide(scope=Scope.APP)
    def get_bytes(self) -> bytes:
        return b"sync"

    @provide(scope=Scope.APP)
    async def get_str(self, a: int, b: float, c: bytes) -> str:
        return f"{a}-{b}-{c!r}"


@pytest.mark.asyncio
async def test_mixed_sync_async_deps():
    container = make_async_container(MixedSyncAsyncProvider())
    result, elapsed = await _timed_get(container, str)
    assert result == "1-2.0-b'sync'"
    _assert_fast(elapsed, 0.15)
    await container.close()


class CachedGatherProvider(Provider):
    def __init__(self, mock: Mock):
        super().__init__()
        self.mock = mock

    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        self.mock()
        await asyncio.sleep(0.05)
        return 1

    @provide(scope=Scope.APP)
    async def get_float(self) -> float:
        await asyncio.sleep(0.05)
        return 2.0

    @provide(scope=Scope.APP)
    async def get_str(self, a: int, b: float) -> str:
        return f"{a}-{b}"


@pytest.mark.asyncio
async def test_cached_deps_not_recreated():
    mock = Mock()
    container = make_async_container(CachedGatherProvider(mock))

    result1 = await container.get(str)
    result2 = await container.get(str)
    assert result1 == result2 == "1-2.0"
    mock.assert_called_once()
    await container.close()


@pytest.mark.asyncio
async def test_gather_works_without_lock():
    container = make_async_container(
        IndependentDepsProvider(),
        lock_factory=None,
    )
    result, elapsed = await _timed_get(container, str)
    assert result == "1-2.0"
    _assert_fast(elapsed, 0.15)
    await container.close()


class KwOnlyDepsProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.1)
        return 10

    @provide(scope=Scope.APP)
    async def get_float(self) -> float:
        await asyncio.sleep(0.1)
        return 1.5

    @provide(scope=Scope.APP)
    async def get_str(self, *, a: int, b: float) -> str:
        return f"{a}+{b}"


@pytest.mark.asyncio
async def test_keyword_only_deps_gathered():
    container = make_async_container(KwOnlyDepsProvider())
    result, elapsed = await _timed_get(container, str)
    assert result == "10+1.5"
    _assert_fast(elapsed, 0.15)
    await container.close()


class MixedScopeProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.05)
        return 1

    @provide(scope=Scope.REQUEST)
    async def get_float(self) -> float:
        await asyncio.sleep(0.05)
        return 2.0

    @provide(scope=Scope.REQUEST)
    async def get_str(self, a: int, b: float) -> str:
        return f"{a}-{b}"


@pytest.mark.asyncio
async def test_mixed_scopes():
    container = make_async_container(MixedScopeProvider())
    async with container(scope=Scope.REQUEST) as request_container:
        result = await request_container.get(str)
        assert result == "1-2.0"
    await container.close()


class ErrorProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.05)
        msg = "int factory failed"
        raise ValueError(msg)

    @provide(scope=Scope.APP)
    async def get_float(self) -> float:
        await asyncio.sleep(0.05)
        return 2.0

    @provide(scope=Scope.APP)
    async def get_str(self, a: int, b: float) -> str:
        return f"{a}-{b}"


@pytest.mark.asyncio
async def test_error_propagation():
    container = make_async_container(ErrorProvider())
    with pytest.raises(ValueError, match="int factory failed"):
        await container.get(str)
    await container.close()


class ConcurrentAccessProvider(Provider):
    def __init__(self, call_counts: dict):
        super().__init__()
        self.call_counts = call_counts

    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        self.call_counts["int"] = self.call_counts.get("int", 0) + 1
        await asyncio.sleep(0.05)
        return 1

    @provide(scope=Scope.APP)
    async def get_float(self) -> float:
        self.call_counts["float"] = self.call_counts.get("float", 0) + 1
        await asyncio.sleep(0.05)
        return 2.0

    @provide(scope=Scope.APP)
    async def get_str(self, a: int, b: float) -> str:
        return f"{a}-{b}"


@pytest.mark.asyncio
async def test_concurrent_container_access():
    call_counts: dict = {}
    container = make_async_container(ConcurrentAccessProvider(call_counts))

    results = await asyncio.gather(
        container.get(str),
        container.get(str),
        container.get(str),
    )
    for r in results:
        assert r == "1-2.0"
    await container.close()


class SingleAsyncDepProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.05)
        return 42

    @provide(scope=Scope.APP)
    async def get_str(self, a: int) -> str:
        return str(a)


@pytest.mark.asyncio
async def test_single_async_dep():
    container = make_async_container(SingleAsyncDepProvider())
    result = await container.get(str)
    assert result == "42"
    await container.close()


class MixedPosKwProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.1)
        return 5

    @provide(scope=Scope.APP)
    async def get_float(self) -> float:
        await asyncio.sleep(0.1)
        return 1.5

    @provide(scope=Scope.APP)
    async def get_bytes(self) -> bytes:
        await asyncio.sleep(0.1)
        return b"data"

    @provide(scope=Scope.APP)
    async def get_str(self, a: int, *, b: float, c: bytes) -> str:
        return f"{a}-{b}-{c!r}"


@pytest.mark.asyncio
async def test_mixed_positional_and_keyword():
    container = make_async_container(MixedPosKwProvider())
    result, elapsed = await _timed_get(container, str)
    assert result == "5-1.5-b'data'"
    _assert_fast(elapsed, 0.15)
    await container.close()


class AllSyncInAsyncProvider(Provider):
    @provide(scope=Scope.APP)
    def get_int(self) -> int:
        return 1

    @provide(scope=Scope.APP)
    def get_float(self) -> float:
        return 2.0

    @provide(scope=Scope.APP)
    def get_str(self, a: int, b: float) -> str:
        return f"{a}-{b}"


@pytest.mark.asyncio
async def test_all_sync_in_async_container():
    container = make_async_container(AllSyncInAsyncProvider())
    result = await container.get(str)
    assert result == "1-2.0"
    await container.close()


# --- Diamond pattern (shared transitive dep) tests ---


class DiamondSingleCreationProvider(DiamondConsumersMixin, Provider):
    def __init__(self, call_counts: dict):
        super().__init__()
        self.call_counts = call_counts

    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        self.call_counts["int"] = self.call_counts.get("int", 0) + 1
        await asyncio.sleep(0.1)
        return 42


@pytest.mark.asyncio
async def test_diamond_single_creation():
    """Shared dep (int) is created once via pending sentinel."""
    call_counts: dict = {}
    container = make_async_container(
        DiamondSingleCreationProvider(call_counts),
    )
    result = await container.get(bytes)
    assert result == b"42.0-42"
    assert call_counts["int"] == 1
    await container.close()


class DiamondTimingProvider(DiamondConsumersMixin, Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.1)
        return 1

    @provide(scope=Scope.APP)
    async def get_float(self, v: int) -> float:
        await asyncio.sleep(0.1)
        return float(v)

    @provide(scope=Scope.APP)
    async def get_str(self, v: int) -> str:
        await asyncio.sleep(0.1)
        return str(v)

    @provide(scope=Scope.APP)
    async def get_bytes(self, a: float, b: str) -> bytes:
        return f"{a}-{b}".encode()


@pytest.mark.asyncio
async def test_diamond_concurrent_timing():
    """Diamond deps (float, str) are gathered concurrently."""
    container = make_async_container(DiamondTimingProvider())
    result, elapsed = await _timed_get(container, bytes)
    assert result == b"1.0-1"
    # Sequential: int(0.1) + float(0.1) + str(0.1) = 0.3s
    # Gathered: int(0.1) + max(float(0.1), str(0.1)) = 0.2s
    _assert_fast(elapsed, 0.25, "diamond should be gathered")
    await container.close()


class DiamondErrorProvider(DiamondConsumersMixin, Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.05)
        msg = "shared dep failed"
        raise ValueError(msg)


@pytest.mark.asyncio
async def test_diamond_error_propagation():
    """Error in shared transitive dep propagates correctly through gather."""
    container = make_async_container(DiamondErrorProvider())
    with pytest.raises(ValueError, match="shared dep failed"):
        await container.get(bytes)
    await container.close()


class DiamondAsyncGeneratorProvider(DiamondConsumersMixin, Provider):
    def __init__(self, call_counts: dict):
        super().__init__()
        self.call_counts = call_counts

    @provide(scope=Scope.APP)
    async def get_int(self) -> AsyncIterator[int]:
        self.call_counts["int"] = self.call_counts.get("int", 0) + 1
        await asyncio.sleep(0.05)
        yield 42


@pytest.mark.asyncio
async def test_diamond_async_generator_cached():
    """Shared async generator dep is created once, exit registered once."""
    call_counts: dict = {}
    container = make_async_container(
        DiamondAsyncGeneratorProvider(call_counts),
    )
    result = await container.get(bytes)
    assert result == b"42.0-42"
    assert call_counts["int"] == 1
    await container.close()


# --- cache=False shared transitive dep tests ---


class DiamondUncachedFactoryProvider(DiamondConsumersMixin, Provider):
    def __init__(self, call_counts: dict):
        super().__init__()
        self.call_counts = call_counts
        self._counter = 0

    @provide(scope=Scope.APP, cache=False)
    async def get_int(self) -> int:
        self.call_counts["int"] = self.call_counts.get("int", 0) + 1
        self._counter += 1
        await asyncio.sleep(0.1)
        return self._counter


@pytest.mark.asyncio
async def test_diamond_uncached_factory_creates_per_consumer():
    """cache=False shared dep is created independently per consumer branch."""
    call_counts: dict = {}
    container = make_async_container(
        DiamondUncachedFactoryProvider(call_counts),
    )
    await container.get(bytes)
    assert call_counts["int"] == 2
    await container.close()


@pytest.mark.asyncio
async def test_diamond_uncached_factory_concurrent_timing():
    """cache=False shared dep branches run concurrently when gathered."""
    call_counts: dict = {}
    container = make_async_container(
        DiamondUncachedFactoryProvider(call_counts),
    )
    _result, elapsed = await _timed_get(container, bytes)
    # Sequential: int(0.1) + int(0.1) = 0.2s
    # Gathered: max(int(0.1), int(0.1)) = 0.1s
    _assert_fast(elapsed, 0.15, "should gather uncached")
    assert call_counts["int"] == 2
    await container.close()


class DiamondUncachedAsyncGenProvider(DiamondConsumersMixin, Provider):
    def __init__(self, call_counts: dict, closed: list):
        super().__init__()
        self.call_counts = call_counts
        self.closed = closed
        self._counter = 0

    @provide(scope=Scope.APP, cache=False)
    async def get_int(self) -> AsyncIterator[int]:
        self.call_counts["int"] = self.call_counts.get("int", 0) + 1
        self._counter += 1
        val = self._counter
        await asyncio.sleep(0.05)
        yield val
        self.closed.append(val)


@pytest.mark.asyncio
async def test_diamond_uncached_async_generator_per_consumer():
    """cache=False async generator: each branch gets own instance."""
    call_counts: dict = {}
    closed: list = []
    container = make_async_container(
        DiamondUncachedAsyncGenProvider(call_counts, closed),
    )
    await container.get(bytes)
    assert call_counts["int"] == 2
    await container.close()
    assert len(closed) == 2


class DiamondUncachedErrorProvider(DiamondConsumersMixin, Provider):
    @provide(scope=Scope.APP, cache=False)
    async def get_int(self) -> int:
        await asyncio.sleep(0.05)
        msg = "uncached dep fails"
        raise ValueError(msg)


@pytest.mark.asyncio
async def test_diamond_uncached_error_one_branch():
    """cache=False shared dep: error propagates correctly through gather."""
    container = make_async_container(DiamondUncachedErrorProvider())
    with pytest.raises(ValueError, match="uncached dep fails"):
        await container.get(bytes)
    await container.close()


class DiamondMixedCacheProvider(DiamondConsumersMixin, Provider):
    def __init__(self, call_counts: dict):
        super().__init__()
        self.call_counts = call_counts
        self._uncached_counter = 0

    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        self.call_counts["int"] = self.call_counts.get("int", 0) + 1
        await asyncio.sleep(0.05)
        return 42

    @provide(scope=Scope.APP, cache=False)
    async def get_complex(self) -> complex:
        self.call_counts["complex"] = self.call_counts.get("complex", 0) + 1
        self._uncached_counter += 1
        await asyncio.sleep(0.1)
        return complex(self._uncached_counter, 0)

    @provide(scope=Scope.APP)
    async def get_float(self, v: int, c: complex) -> float:
        return float(v) + c.real

    @provide(scope=Scope.APP)
    async def get_str(self, v: int, c: complex) -> str:
        return f"{v}+{c.real}"

    @provide(scope=Scope.APP)
    async def get_bytes(self, a: float, b: str) -> bytes:
        return f"{a}-{b}".encode()


@pytest.mark.asyncio
async def test_diamond_mixed_cached_uncached():
    """Mixed diamond: float and str branches run concurrently.

    int is cached (created once via pending sentinel), complex is uncached
    (created per branch). Timing proves concurrency: sequential would take
    int(0.05) + complex(0.1) + complex(0.1) = 0.25s; gathered takes
    int(0.05) + max(complex(0.1), complex(0.1)) = 0.15s.
    """
    call_counts: dict = {}
    container = make_async_container(DiamondMixedCacheProvider(call_counts))
    _result, elapsed = await _timed_get(container, bytes)
    assert call_counts["int"] == 1  # cached — created once
    assert call_counts["complex"] == 2  # uncached — created per branch
    _assert_fast(elapsed, 0.2, "should gather mixed")
    await container.close()
