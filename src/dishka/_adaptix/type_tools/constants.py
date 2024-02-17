import collections
import concurrent.futures
import queue
import re
from os import PathLike
from typing import Mapping, TypeVar

from ..common import VarTuple

_AnyStrT = TypeVar('_AnyStrT', str, bytes)
_T1 = TypeVar('_T1')
_T2 = TypeVar('_T2')
_T1_co = TypeVar('_T1_co', covariant=True)
_AnyStr_co = TypeVar("_AnyStr_co", str, bytes, covariant=True)

BUILTIN_ORIGIN_TO_TYPEVARS: Mapping[type, VarTuple[TypeVar]] = {
    re.Pattern: (_AnyStrT, ),  # type: ignore[dict-item]
    re.Match: (_AnyStrT, ),  # type: ignore[dict-item]
    PathLike: (_AnyStr_co, ),  # type: ignore[dict-item]
    type: (_T1,),  # type: ignore[dict-item]
    list: (_T1,),  # type: ignore[dict-item]
    set: (_T1,),  # type: ignore[dict-item]
    frozenset: (_T1_co, ),  # type: ignore[dict-item]
    collections.Counter: (_T1,),  # type: ignore[dict-item]
    collections.deque: (_T1,),  # type: ignore[dict-item]
    dict: (_T1, _T2),  # type: ignore[dict-item]
    collections.defaultdict: (_T1, _T2),  # type: ignore[dict-item]
    collections.OrderedDict: (_T1, _T2),  # type: ignore[dict-item]
    collections.ChainMap: (_T1, _T2),  # type: ignore[dict-item]
    queue.Queue: (_T1, ),  # type: ignore[dict-item]
    queue.PriorityQueue: (_T1, ),  # type: ignore[dict-item]
    queue.LifoQueue: (_T1, ),  # type: ignore[dict-item]
    queue.SimpleQueue: (_T1, ),  # type: ignore[dict-item]
    concurrent.futures.Future: (_T1, ),  # type: ignore[dict-item]
}
