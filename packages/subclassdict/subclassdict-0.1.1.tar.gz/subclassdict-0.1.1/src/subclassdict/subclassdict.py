"""SubclassDict: A TypeDict that allows subclasses of type keys to be used as keys."""

from __future__ import annotations

from typing import Any, Hashable, TypeVar, cast

from typedict import TypeDict  # type: ignore[import-untyped]

T = TypeVar("T")


class HashableType(Hashable, type):  # type: ignore[misc]
    """A type that is both hashable and a type."""


class SubclassDict(TypeDict[T]):
    """
    A TypeDict that allows subclasses of type keys to be used as keys.

    When a key is not found, it will look for the closest superclass key.
    This allows for polymorphic behavior where subclasses can access
    values stored under their parent class keys.

    Example:
        >>> class Animal: pass
        >>> class Dog(Animal): pass
        >>> d = SubclassDict()
        >>> d[Animal] = "animal"
        >>> d[Dog]  # Returns "animal" because Dog is a subclass of Animal
        'animal'
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the SubclassDict with optional initial data."""
        self._subclass_cache: dict[HashableType, HashableType | None] = {}
        super().__init__(*args, **kwargs)

    def __getitem__(self, key: HashableType) -> T:
        """
        Get item by key, looking up subclass hierarchy if key not found.

        Args:
            key: The type key to look up

        Returns:
            The value associated with the key or its closest superclass

        Raises:
            KeyError: If neither the key nor any of its superclasses are found
        """
        try:
            return cast(T, super().__getitem__(key))
        except KeyError as e:
            super_key = self._get_super_key(key)
            if super_key is not None:
                return cast(T, super().__getitem__(super_key))
            raise KeyError(key) from e

    def __setitem__(self, key: HashableType, value: T) -> None:
        """
        Set item by key.

        Args:
            key: The type key to set
            value: The value to associate with the key
        """
        # Clear cache for this key and any keys that might be affected
        self._invalidate_cache_for_key(key)
        super().__setitem__(key, value)

    def __delitem__(self, key: HashableType) -> None:
        """
        Delete item by key.

        Args:
            key: The type key to delete

        Raises:
            KeyError: If the key is not found
        """
        # Clear cache for this key and any keys that might be affected
        self._invalidate_cache_for_key(key)
        super().__delitem__(key)

    def __contains__(self, key: HashableType) -> bool:
        """
        Check if key exists (either directly or through subclass lookup).

        Args:
            key: The type key to check

        Returns:
            True if the key exists directly or through subclass lookup
        """
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key: HashableType, default: T | None = None) -> T | None:
        """
        Get item by key with default value.

        Args:
            key: The type key to look up
            default: Default value if key not found

        Returns:
            The value associated with the key or default
        """
        try:
            return self[key]
        except KeyError:
            return default

    def setdefault(self, key: HashableType, default: T | None = None) -> T | None:
        """
        Set default value for key if key not present.

        Args:
            key: The type key to set default for
            default: Default value to set if key not present

        Returns:
            The value associated with the key (existing or newly set)
        """
        if key not in self:
            self[key] = default  # type: ignore[assignment]
        return self[key]

    def pop(self, key: HashableType, default: T | None = None) -> T | None:
        """
        Pop item by key with default value.

        Args:
            key: The type key to pop
            default: Default value if key not found

        Returns:
            The value associated with the key or default
        """
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError:
            if default is not None:
                return default
            raise

    def popitem(self) -> tuple[HashableType, T]:
        """
        Pop an arbitrary item from the dict.

        Returns:
            A tuple of (key, value)

        Raises:
            KeyError: If the dict is empty
        """
        if not self:
            raise KeyError("popitem(): dictionary is empty")
        key = next(iter(self))
        value = self[key]
        del self[key]
        return key, value

    def copy(self) -> SubclassDict[T]:
        """
        Create a shallow copy of the SubclassDict.

        Returns:
            A new SubclassDict with the same items
        """
        new_dict: SubclassDict[T] = SubclassDict()
        new_dict.update(self)
        return new_dict

    def clear(self) -> None:
        """Clear all items and reset the cache."""
        self._subclass_cache.clear()
        super().clear()

    def _get_super_key(self, key: HashableType) -> HashableType | None:
        """
        Find the closest superclass key for the given key.

        Args:
            key: The type key to find a superclass for

        Returns:
            The closest superclass key or None if not found
        """
        # Check cache first
        if key in self._subclass_cache:
            cached_result = self._subclass_cache[key]
            if cached_result is None or cached_result in self:
                return cached_result

        # Find the closest superclass by checking all possible superclasses
        # and finding the one with the shortest MRO distance
        best_key = None
        best_distance = float("inf")

        for existing_key in self.keys():
            if issubclass(key, existing_key):
                # Calculate MRO distance (how many steps up the hierarchy)
                try:
                    mro = key.__mro__
                    distance = mro.index(existing_key)
                    if distance < best_distance:
                        best_distance = distance
                        best_key = existing_key
                except (ValueError, AttributeError):
                    # Fallback: if MRO doesn't work, use first match
                    if best_key is None:
                        best_key = existing_key

        if best_key is not None:
            self._subclass_cache[key] = best_key
            return cast(HashableType, best_key)

        # Cache negative result
        self._subclass_cache[key] = None
        return None

    def _invalidate_cache_for_key(self, key: HashableType) -> None:
        """
        Invalidate cache entries that might be affected by changes to the given key.

        Args:
            key: The key that was changed
        """
        # Remove cache entries for keys that are subclasses of the changed key
        keys_to_remove: list[HashableType] = [
            cached_key
            for cached_key in self._subclass_cache
            if cached_key != key and issubclass(cached_key, key)
        ]
        for cached_key in keys_to_remove:
            del self._subclass_cache[cached_key]
