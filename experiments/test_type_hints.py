"""Experiment to understand how type hints work with FromDishka[WebSocket]"""
from typing import Annotated, get_type_hints, get_origin, get_args
from fastapi import WebSocket, Request
from dishka import FromDishka

def test_func_with_plain_websocket(websocket: WebSocket) -> None:
    pass

def test_func_with_fromdishka_websocket(ws: FromDishka[WebSocket]) -> None:
    pass

def test_func_with_both(websocket: WebSocket, ws: FromDishka[WebSocket]) -> None:
    pass

print("=" * 60)
print("Test 1: Plain WebSocket parameter")
print("=" * 60)
hints1 = get_type_hints(test_func_with_plain_websocket)
print(f"Type hints: {hints1}")
for name, hint in hints1.items():
    print(f"  {name}: {hint}")
    print(f"    is WebSocket: {hint is WebSocket}")
    print(f"    origin: {get_origin(hint)}")

print("\n" + "=" * 60)
print("Test 2: FromDishka[WebSocket] parameter")
print("=" * 60)
hints2 = get_type_hints(test_func_with_fromdishka_websocket, include_extras=True)
print(f"Type hints: {hints2}")
for name, hint in hints2.items():
    print(f"  {name}: {hint}")
    print(f"    is WebSocket: {hint is WebSocket}")
    print(f"    origin: {get_origin(hint)}")
    print(f"    args: {get_args(hint)}")
    if get_origin(hint) is Annotated:
        args = get_args(hint)
        print(f"    First arg (type): {args[0]}")
        print(f"    First arg is WebSocket: {args[0] is WebSocket}")

print("\n" + "=" * 60)
print("Test 3: Both parameters")
print("=" * 60)
hints3 = get_type_hints(test_func_with_both, include_extras=True)
print(f"Type hints: {hints3}")
for name, hint in hints3.items():
    print(f"  {name}: {hint}")
    print(f"    is WebSocket: {hint is WebSocket}")
    print(f"    origin: {get_origin(hint)}")
    if get_origin(hint) is Annotated:
        args = get_args(hint)
        print(f"    First arg (type): {args[0]}")
        print(f"    First arg is WebSocket: {args[0] is WebSocket}")
