from abc import ABC, ABCMeta
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Final,
    Generic,
    Protocol,
    TypeAlias,
    TypeVar,
)

from dishka._adaptix.common import TypeHint
from dishka._adaptix.feature_requirement import HAS_PY_311
from dishka._adaptix.type_tools import (
    get_generic_args,
    get_type_vars,
    is_parametrized,
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
TypeVarsMap: TypeAlias = dict[TypeHint, TypeHint]


def has_orig_bases(obj: TypeHint) -> bool:
    return hasattr(obj, "__orig_bases__")

if HAS_PY_311:
    def is_type_var_tuple(obj: TypeHint) -> bool:
        return getattr(obj, "__typing_is_unpacked_typevartuple__", False)
else:
    def is_type_var_tuple(obj: TypeHint) -> bool:
        return False

def is_ignored_type(origin_obj: TypeHint) -> bool:
    return origin_obj in IGNORE_TYPES


def get_filled_arguments(obj: TypeHint) -> list[TypeHint]:
    filled_arguments = []
    for arg in get_generic_args(obj):
        if isinstance(arg, TypeVar):
            continue
        if is_type_var_tuple(arg):
           continue
        filled_arguments.append(arg)
    return filled_arguments


def create_type_vars_map(obj: TypeHint) -> TypeVarsMap:
    origin_obj = strip_alias(obj)
    if not get_type_vars(origin_obj):
        return {}

    type_vars = list(get_type_vars(origin_obj))
    filled_arguments = get_filled_arguments(obj)

    if not filled_arguments or not type_vars:
        return {}

    type_vars_map = {}
    reversed_arguments = False
    while True:
        if len(type_vars) == 0:
            break
        type_var = type_vars[0]
        if isinstance(type_var, TypeVar):
            del type_vars[0]
            type_vars_map[type_var] = filled_arguments.pop(0)
        else:
            if len(type_vars) == 1:
                if reversed_arguments:
                    filled_arguments.reverse()
                type_vars_map[type_var] = filled_arguments
                break
            type_vars.reverse()
            filled_arguments.reverse()
            reversed_arguments = not reversed_arguments

    return type_vars_map


def create_type(
    obj: TypeHint,
    type_vars_map: TypeVarsMap,
) -> TypeHint:
    origin_obj = strip_alias(obj)
    type_vars = get_type_vars(origin_obj) or get_type_vars(obj)
    if not type_vars:
        return origin_obj

    generic_args = []
    for type_var in type_vars:
        arg = type_vars_map[type_var]
        if isinstance(arg, list):
            generic_args.extend(arg)
        else:
            generic_args.append(arg)
    return origin_obj[tuple(generic_args)]


def recursion_get_parents_for_generic_class(
    obj: TypeHint,
    parents: list[TypeHint],
    type_vars_map: TypeVarsMap,
) -> None:
    origin_obj = strip_alias(obj)
    if not has_orig_bases(origin_obj):
        parents.extend(get_parents_for_mro(origin_obj))
        return

    for obj_ in origin_obj.__orig_bases__:
        origin_obj = strip_alias(obj_)
        if is_ignored_type(origin_obj):
            continue

        type_vars_map.update(create_type_vars_map(obj_))
        parents.append(create_type(obj_, type_vars_map))
        recursion_get_parents_for_generic_class(
            obj_,
            parents,
            type_vars_map.copy(),
        )


def get_parents_for_mro(obj: TypeHint) -> list[TypeHint]:
    return [
        obj_ for obj_ in obj.mro()
        if not is_ignored_type(strip_alias(obj_))
    ]


def get_parents(obj: TypeHint) -> list[TypeHint]:
    if is_ignored_type(strip_alias(obj)):
        raise ValueError(f"The starting class {obj!r} is in ignored types")

    if is_parametrized(obj):
        type_vars_map = create_type_vars_map(obj)
        parents = [
            create_type(
                obj=obj,
                type_vars_map=type_vars_map,
            ),
        ]
        recursion_get_parents_for_generic_class(
            obj=obj,
            parents=parents,
            type_vars_map=type_vars_map,
        )
    elif has_orig_bases(obj):
        parents = [obj]
        recursion_get_parents_for_generic_class(
            obj=obj,
            parents=parents,
            type_vars_map={},
        )
    else:
        parents = get_parents_for_mro(obj)
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
            return parents[0]
