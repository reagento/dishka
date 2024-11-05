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
from dishka._adaptix.type_tools.basic_utils import is_parametrized
from dishka._adaptix.type_tools.fundamentals import (
    get_generic_args,
    get_type_vars,
    strip_alias,
)
from dishka.entities.provides_marker import ProvideMultiple

__all__ = ["WithParents", "ParentsResolver"]

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

if HAS_PY_311:
    def is_type_var_tuple(obj: TypeHint) -> bool:
        return getattr(obj, "__typing_is_unpacked_typevartuple__", False)
else:
    def is_type_var_tuple(obj: TypeHint) -> bool:
        return False


def has_orig_bases(obj: TypeHint) -> bool:
    return hasattr(obj, "__orig_bases__")


def is_ignored_type(origin_type: TypeHint) -> bool:
    return origin_type in IGNORE_TYPES


def create_type_vars_map(obj: TypeHint) -> dict[TypeHint, TypeHint]:
    origin_obj = strip_alias(obj)
    type_vars = list(get_type_vars(origin_obj) or get_type_vars(obj))
    if not type_vars:
        return {}

    type_vars_map = {}
    arguments = list(get_generic_args(obj))
    reversed_arguments = False
    while True:
        if len(type_vars) == 0:
            break

        type_var = type_vars[0]
        if isinstance(type_var, TypeVar):
            del type_vars[0]
            type_vars_map[type_var] = arguments.pop(0)
        else:
            if len(type_vars) == 1:
                if reversed_arguments:
                    arguments.reverse()
                type_vars_map[type_var] = arguments
                break
            type_vars.reverse()
            arguments.reverse()
            reversed_arguments = not reversed_arguments

    return type_vars_map



class ParentsResolver:
    def get_parents(self, child_type: TypeHint) -> list[TypeHint]:
        if is_ignored_type(strip_alias(child_type)):
            raise ValueError(
                f"The starting class {child_type!r} is in ignored types",
            )
        if is_parametrized(child_type) or has_orig_bases(child_type):
            return self._get_parents_for_generic(child_type)
        return self._get_parents_for_mro(child_type)

    def _get_parents_for_generic(
        self, child_type: TypeHint,
    ) -> list[TypeHint]:
        parents: list[TypeHint] = []
        self._recursion_get_parents(
            child_type=child_type,
            parents=parents,
            type_vars_map={},
        )
        return parents

    def _recursion_get_parents(
        self,
        child_type: TypeHint,
        parents: list[TypeHint],
        type_vars_map: TypeVarsMap,
    ) -> None:
        origin_child_type = strip_alias(child_type)
        parametrized = is_parametrized(child_type)
        orig_bases = has_orig_bases(origin_child_type)
        if not orig_bases and not parametrized:
            parents.extend(
                self._get_parents_for_mro(origin_child_type),
            )
            return

        new_type_vars_map = create_type_vars_map(child_type)
        new_type_vars_map.update(type_vars_map)
        parents.append(
            self._create_type(
                obj=child_type,
                type_vars_map=new_type_vars_map,
            ),
        )
        if not orig_bases:
            return
        for parent_type in origin_child_type.__orig_bases__:
            origin_parent_type = strip_alias(parent_type)
            if is_ignored_type(origin_parent_type):
                continue

            self._recursion_get_parents(
                child_type=parent_type,
                parents=parents,
                type_vars_map=new_type_vars_map,
            )

    def _get_parents_for_mro(
        self, child_type: TypeHint,
    ) -> list[TypeHint]:
        return [
            parent_type for parent_type in child_type.mro()
            if not is_ignored_type(strip_alias(parent_type))
        ]

    def _create_type(
        self,
        obj: TypeHint,
        type_vars_map: TypeVarsMap,
    ) -> TypeHint:
        origin_obj = strip_alias(obj)
        type_vars = get_type_vars(origin_obj) or get_type_vars(obj)
        if not type_vars:
            return obj

        generic_args = []
        for type_var in type_vars:
            arg = type_vars_map[type_var]
            if isinstance(arg, list):
                generic_args.extend(arg)
            else:
                generic_args.append(arg)
        return origin_obj[tuple(generic_args)]


if TYPE_CHECKING:
    T = TypeVar("T")
    WithParents: TypeAlias = T | T  # noqa: PYI016
else:
    class WithParents:
        def __class_getitem__(cls, item: TypeHint) -> TypeHint:
            parents = ParentsResolver().get_parents(item)
            if len(parents) > 1:
                return ProvideMultiple[tuple(parents)]
            return parents[0]
