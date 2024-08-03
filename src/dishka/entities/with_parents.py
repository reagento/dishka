from abc import ABC, ABCMeta
from enum import Enum
from types import GenericAlias
from typing import (
    TYPE_CHECKING,
    Final,
    Generic,
    Protocol,
    TypeAlias,
    TypeVar,
    TypeVarTuple,
    cast,
)

from dishka._adaptix.common import TypeHint
from dishka._adaptix.type_tools import (
    get_generic_args,
    get_type_vars,
    is_generic,
    is_named_tuple_class,
    is_protocol,
    is_typed_dict_class,
    strip_alias,
)
from dishka.entities.provides_marker import ProvideMultiple

IGNORE_TYPES: Final = (
    type,
    object,
    Enum,
    ABC,
    ABCMeta,
    Generic,
    Protocol,
    Exception,
    BaseException,
)
TypeVarsMap: TypeAlias = dict[TypeVar | TypeVarTuple, TypeHint]


def is_ignore_type(origin_obj: TypeHint) -> bool:
    if origin_obj in IGNORE_TYPES:
        return True
    if is_protocol(origin_obj):
        return True
    if is_named_tuple_class(origin_obj):
        return True
    if is_typed_dict_class(origin_obj):
        return True
    return False


def get_filled_arguments(obj: TypeHint) -> list[TypeHint]:
    return [
        arg
        for arg in get_generic_args(obj)
        if not isinstance(arg, (TypeVar, TypeVarTuple))
    ]


def create_type_vars_map(obj: TypeHint) -> TypeVarsMap:
    origin_obj = strip_alias(obj)
    if not get_type_vars(origin_obj):
        return {}

    type_vars_map = {}
    type_vars = list(get_type_vars(origin_obj))
    filled_arguments = get_filled_arguments(obj)
    if not filled_arguments or not type_vars:
        return {}

    while True:
        if len(type_vars) == 0:
            break
        type_var = type_vars[0]
        if isinstance(type_var, TypeVarTuple):
            type_vars.reverse()
            if len(type_vars) == 1:
                type_vars_map[type_var] = filled_arguments
                break
            filled_arguments.reverse()
        else:
            del type_vars[0]
            type_vars_map[type_var] = filled_arguments.pop(0)
    return cast(TypeVarsMap, type_vars_map)


def create_generic_class(
    origin_obj: TypeHint,
    type_vars_map: TypeVarsMap,
) -> TypeHint | None:
    if is_generic(origin_obj):
        generic_args = []
        for type_var in get_type_vars(origin_obj):
            arg = type_vars_map[type_var]
            if isinstance(arg, list):
                generic_args.extend(arg)
            else:
                generic_args.append(arg)
        return origin_obj[*generic_args]
    return None


def recursion_get_parents_for_generic_class(
    obj: TypeHint,
    parents: list[TypeHint],
    type_vars_map: TypeVarsMap,
) -> None:
    origin_obj = strip_alias(obj)
    if is_ignore_type(origin_obj):
        return

    type_vars_map.update(create_type_vars_map(obj))
    for obj in origin_obj.__orig_bases__:
        origin_obj = strip_alias(obj)
        if is_ignore_type(origin_obj):
            continue

        type_vars_map.update(create_type_vars_map(obj))
        parents.append(create_generic_class(origin_obj, type_vars_map) or obj)
        recursion_get_parents_for_generic_class(
            obj,
            parents,
            type_vars_map.copy(),
        )


def get_parents(obj: TypeHint) -> list[TypeHint]:
    if is_ignore_type(strip_alias(obj)):
        raise ValueError("The starting class %r is in ignored types" % obj)

    if isinstance(obj, GenericAlias):
        type_vars_map = create_type_vars_map(obj)
        parents = [
            create_generic_class(
                origin_obj=strip_alias(obj),
                type_vars_map=type_vars_map,
            ) or obj,
        ]
        recursion_get_parents_for_generic_class(
            obj=obj,
            parents=parents,
            type_vars_map=type_vars_map,
        )
    elif hasattr(obj, "__orig_bases__"):
        parents = [obj]
        recursion_get_parents_for_generic_class(
            obj=obj,
            parents=parents,
            type_vars_map={},
        )
    else:
        parents = [
            obj_ for obj_ in obj.mro()
            if not is_ignore_type(strip_alias(obj_))
        ]
    return parents


if TYPE_CHECKING:
    from typing import Union as WithParents
else:
    class WithParents:
        def __class_getitem__(
            cls, item: TypeHint,
        ) -> TypeHint | ProvideMultiple:
            parents = get_parents(item)
            if len(parents) > 1:
                return ProvideMultiple(parents)
            return item
