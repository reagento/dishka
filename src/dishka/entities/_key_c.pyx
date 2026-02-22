from typing import Any, Literal, TypeVar, get_args, get_origin

from .marker import Marker


cdef class DependencyKey:
    cdef readonly object type_hint
    cdef readonly object component
    cdef readonly int depth

    def __cinit__(self, object type_hint, object component, int depth=0):
        self.type_hint = type_hint
        self.component = component
        self.depth = depth

    def __hash__(self):
        return hash((self.type_hint, self.component, self.depth))

    def __richcmp__(self, object other, int op):
        cdef object left_tuple = (self.type_hint, self.component, self.depth)
        cdef object right_tuple

        if isinstance(other, DependencyKey):
            right_tuple = (other.type_hint, other.component, other.depth)
        elif isinstance(other, tuple) and len(other) == 3:
            right_tuple = other
        else:
            right_tuple = NotImplemented

        if right_tuple is NotImplemented:
            return NotImplemented
        if op == 2:
            return left_tuple == right_tuple
        if op == 3:
            return left_tuple != right_tuple
        return NotImplemented

    def __iter__(self):
        return iter((self.type_hint, self.component, self.depth))

    def __len__(self):
        return 3

    def __getitem__(self, object index):
        return (self.type_hint, self.component, self.depth)[index]

    def __reduce__(self):
        return (DependencyKey, (self.type_hint, self.component, self.depth))

    def __repr__(self):
        return (
            "DependencyKey("
            f"type_hint={self.type_hint!r}, "
            f"component={self.component!r}, "
            f"depth={self.depth!r})"
        )

    def with_component(self, object component):
        if self.component is not None:
            return self
        return DependencyKey(self.type_hint, component, self.depth)

    def __str__(self):
        if self.depth == 0:
            return f"({self.type_hint}, component={self.component!r})"
        return (
            f"({self.type_hint},"
            f" component={self.component!r},"
            f" depth={self.depth})"
        )

    def is_const(self):
        return get_origin(self.type_hint) is Literal and len(get_args(self.type_hint)) == 1

    def is_type_var(self):
        return isinstance(self.type_hint, TypeVar)

    def get_const_value(self):
        return get_args(self.type_hint)[0]

    def is_marker(self):
        return isinstance(self.type_hint, Marker) or (
            isinstance(self.type_hint, type) and issubclass(self.type_hint, Marker)
        )
