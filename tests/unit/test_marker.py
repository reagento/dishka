import pytest

from dishka import Has, Marker
from dishka.entities.marker import BoolMarker


class Child(Marker):
    pass


def test_equal():
    a = Marker("a")
    a2 = Marker("a")
    b = Marker("b")
    c = Child("a")

    assert a == a2
    assert a != b
    assert a != c


def test_child_comparison():
    assert Child("a") == Child("a")
    assert Child("a") != Child("b")


def test_operations():
    a = Marker("a")
    b = Marker("b")

    assert a | a == a
    assert a & a == a
    assert a | b == b | a
    assert a & b == b & a
    assert ~(a | b) == ~a & ~b
    assert ~~a == a
    assert a | b != a


def test_bool():
    true = BoolMarker(True)
    false = BoolMarker(False)
    a = Marker("a")

    assert true != false
    assert ~true == false
    assert true & a == a
    assert false & a == false
    assert true | a == true
    assert false | a == a



@pytest.mark.parametrize(
    ("marker", "repr_value"),
    [
        (Marker("a"), "Marker('a')"),
        (Child("a"), "Child('a')"),
        (~Marker("a"), "~Marker('a')"),
        (Marker("a") | Marker("b"), "(Marker('a') | Marker('b'))"),
        (Marker("a") & Marker("b"), "(Marker('a') & Marker('b'))"),
        (Has(int), "Has(<class 'int'>)"),
    ],
)
def test_repr(marker, repr_value):
    assert repr(marker) == repr_value
