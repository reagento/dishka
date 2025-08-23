from collections.abc import Callable
from typing import TypeVar

from dishka.integrations.aiohttp import AiohttpHandler, inject

_ReturnT = TypeVar("_ReturnT")

def custom_inject(func: Callable[..., _ReturnT]) -> AiohttpHandler:
    func.__custom__ = True
    return inject(func)
