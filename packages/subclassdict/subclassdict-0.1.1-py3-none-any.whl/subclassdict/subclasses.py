"""Utility functions for working with class hierarchies."""

from __future__ import annotations

from itertools import chain
from typing import Any


def subclasses(cls: type[Any]) -> list[type[Any]]:
    """
    Get all subclasses of a class recursively.

    This function recursively traverses the class hierarchy to find all
    subclasses of the given class, including subclasses of subclasses.

    Args:
        cls: The class to find subclasses for

    Returns:
        A list of all subclasses (including subclasses of subclasses)

    Example:
        >>> class Animal: pass
        >>> class Dog(Animal): pass
        >>> class Cat(Animal): pass
        >>> class Puppy(Dog): pass
        >>> subclasses(Animal)
        [Dog, Cat, Puppy]
    """
    return list(
        chain.from_iterable(
            [
                list(chain.from_iterable([[x], subclasses(x)]))
                for x in cls.__subclasses__()
            ]
        )
    )
