from faststream.__about__ import (
    __version__ as FASTSTREAM_VERSION,  # noqa: N812
)

from dishka import FromDishka

FASTSTREAM_05 = FASTSTREAM_VERSION.startswith("0.5")
FASTSTREAM_06 = FASTSTREAM_VERSION.startswith("0.6")

if FASTSTREAM_05:
    from .faststream_05 import FastStreamProvider, inject, setup_dishka
elif FASTSTREAM_06:
    from .faststream_06 import FastStreamProvider, inject, setup_dishka
else:
    raise RuntimeError(  # noqa: TRY003
        f"FastStream {FASTSTREAM_VERSION} version not supported",
    )

__all__ = (
    "FastStreamProvider",
    "FromDishka",
    "inject",
    "setup_dishka",
)
