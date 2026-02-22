from __future__ import annotations

from typing import Any

from wireup import SyncContainer, create_sync_container


def make_wireup_benchmark_container(*injectables: Any) -> SyncContainer:
    return create_sync_container(
        injectables=list(injectables),
        concurrent_scoped_access=False,
    )
