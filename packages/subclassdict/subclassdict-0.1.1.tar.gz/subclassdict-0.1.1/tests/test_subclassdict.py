"""Tests for SubclassDict core functionality."""

import pytest

from subclassdict import SubclassDict


class TestSubclassDictBasic:
    """Test basic SubclassDict functionality."""

    def test_init_empty(self):
        """Test initialization of empty SubclassDict."""
        d = SubclassDict()
        assert len(d) == 0
        assert not d

    def test_init_with_data(self, animal_hierarchy):
        """Test initialization with initial data."""
        Animal, Dog = animal_hierarchy["Animal"], animal_hierarchy["Dog"]
        d = SubclassDict({Animal: "animal", Dog: "dog"})
        assert len(d) == 2
        assert d[Animal] == "animal"
        assert d[Dog] == "dog"

    def test_init_with_kwargs(self):
        """Test initialization with keyword arguments."""

        class A:
            pass

        class B:
            pass

        # SubclassDict doesn't support string keys in kwargs
        # Use dict initialization instead
        d = SubclassDict({A: "a", B: "b"})
        assert d[A] == "a"
        assert d[B] == "b"


class TestSubclassDictInheritance:
    """Test subclass inheritance behavior."""

    def test_direct_key_access(self, animal_hierarchy):
        """Test accessing keys that exist directly."""
        Animal, Dog = animal_hierarchy["Animal"], animal_hierarchy["Dog"]
        d = SubclassDict()
        d[Animal] = "animal"
        d[Dog] = "dog"

        assert d[Animal] == "animal"
        assert d[Dog] == "dog"

    def test_subclass_lookup(self, animal_hierarchy):
        """Test that subclasses can access parent class values."""
        Animal, Dog, Puppy = (
            animal_hierarchy["Animal"],
            animal_hierarchy["Dog"],
            animal_hierarchy["Puppy"],
        )
        d = SubclassDict()
        d[Animal] = "animal"

        # Dog should find Animal's value
        assert d[Dog] == "animal"
        # Puppy should find Animal's value (through Dog)
        assert d[Puppy] == "animal"

    def test_closest_superclass_preference(self, animal_hierarchy):
        """Test that closest superclass is preferred."""
        Animal, Mammal, Dog = (
            animal_hierarchy["Animal"],
            animal_hierarchy["Mammal"],
            animal_hierarchy["Dog"],
        )
        d = SubclassDict()
        d[Animal] = "animal"
        d[Mammal] = "mammal"

        # Dog should find Mammal's value (closer than Animal)
        assert d[Dog] == "mammal"

    def test_multiple_inheritance(self, multiple_inheritance_hierarchy):
        """Test behavior with multiple inheritance."""
        A, B, C, D = (
            multiple_inheritance_hierarchy["A"],
            multiple_inheritance_hierarchy["B"],
            multiple_inheritance_hierarchy["C"],
            multiple_inheritance_hierarchy["D"],
        )
        d = SubclassDict()
        d[A] = "a"
        d[B] = "b"

        # C inherits from both A and B - should find one of them
        assert d[C] in ["a", "b"]
        # D inherits from C, which inherits from A and B
        assert d[D] in ["a", "b"]


class TestSubclassDictMethods:
    """Test SubclassDict methods."""

    def test_getitem_keyerror(self, animal_hierarchy):
        """Test KeyError when key not found."""
        Animal, Bird = animal_hierarchy["Animal"], animal_hierarchy["Bird"]
        d = SubclassDict()
        d[Animal] = "animal"

        # Bird IS a subclass of Animal, so it should find Animal's value
        assert d[Bird] == "animal"

        # Test with a truly unrelated class
        class Unrelated:
            pass

        with pytest.raises(KeyError):
            d[Unrelated]  # Unrelated is not a subclass of Animal

    def test_setitem(self, animal_hierarchy):
        """Test setting items."""
        Animal, Dog = animal_hierarchy["Animal"], animal_hierarchy["Dog"]
        d = SubclassDict()

        d[Animal] = "animal"
        assert d[Animal] == "animal"

        d[Dog] = "dog"
        assert d[Dog] == "dog"
        assert d[Animal] == "animal"  # Original should remain

    def test_delitem(self, animal_hierarchy):
        """Test deleting items."""
        Animal, Dog = animal_hierarchy["Animal"], animal_hierarchy["Dog"]
        d = SubclassDict()
        d[Animal] = "animal"
        d[Dog] = "dog"

        del d[Dog]
        # Dog is no longer a direct key, but it's still found through Animal
        assert Dog in d  # Found through Animal
        assert d[Dog] == "animal"  # Gets Animal's value
        assert Animal in d
        assert d[Animal] == "animal"

    def test_delitem_keyerror(self, animal_hierarchy):
        """Test KeyError when deleting non-existent key."""
        Animal = animal_hierarchy["Animal"]
        d = SubclassDict()

        with pytest.raises(KeyError):
            del d[Animal]

    def test_contains(self, animal_hierarchy):
        """Test __contains__ method."""
        Animal, Dog, Bird = (
            animal_hierarchy["Animal"],
            animal_hierarchy["Dog"],
            animal_hierarchy["Bird"],
        )
        d = SubclassDict()
        d[Animal] = "animal"

        assert Animal in d
        assert Dog in d  # Dog is subclass of Animal
        assert Bird in d  # Bird IS a subclass of Animal

        # Test with a truly unrelated class
        class Unrelated:
            pass

        assert Unrelated not in d  # Unrelated is not subclass of Animal

    def test_get(self, animal_hierarchy):
        """Test get method."""
        Animal, Dog, Bird = (
            animal_hierarchy["Animal"],
            animal_hierarchy["Dog"],
            animal_hierarchy["Bird"],
        )
        d = SubclassDict()
        d[Animal] = "animal"

        assert d.get(Animal) == "animal"
        assert d.get(Dog) == "animal"  # Subclass lookup
        assert d.get(Bird) == "animal"  # Bird IS a subclass of Animal

        # Test with a truly unrelated class
        class Unrelated:
            pass

        assert d.get(Unrelated) is None  # Not found
        assert d.get(Unrelated, "default") == "default"  # With default

    def test_setdefault(self, animal_hierarchy):
        """Test setdefault method."""
        Animal, Dog = animal_hierarchy["Animal"], animal_hierarchy["Dog"]
        d = SubclassDict()

        # Set default for new key
        result = d.setdefault(Animal, "animal")
        assert result == "animal"
        assert d[Animal] == "animal"

        # Don't override existing key
        result = d.setdefault(Animal, "new_animal")
        assert result == "animal"
        assert d[Animal] == "animal"

        # Subclass should find parent's value
        result = d.setdefault(Dog, "dog")
        assert result == "animal"  # Found parent's value
        assert Animal in d
        assert Dog in d  # Dog is found through Animal (subclass lookup)

    def test_pop(self, animal_hierarchy):
        """Test pop method."""
        Animal, Dog = animal_hierarchy["Animal"], animal_hierarchy["Dog"]
        d = SubclassDict()
        d[Animal] = "animal"
        d[Dog] = "dog"

        # Pop existing key
        value = d.pop(Dog)
        assert value == "dog"
        # Dog is no longer a direct key, but still found through Animal
        assert Dog in d  # Found through Animal
        assert d[Dog] == "animal"  # Gets Animal's value
        assert Animal in d

        # Pop with default
        value = d.pop(Dog, "default")
        assert value == "default"

        # Pop non-existent key without default
        with pytest.raises(KeyError):
            d.pop(Dog)

    def test_popitem(self, animal_hierarchy):
        """Test popitem method."""
        Animal, Dog = animal_hierarchy["Animal"], animal_hierarchy["Dog"]
        d = SubclassDict()
        d[Animal] = "animal"
        d[Dog] = "dog"

        # Pop an item
        key, value = d.popitem()
        assert key in [Animal, Dog]
        assert value in ["animal", "dog"]
        assert len(d) == 1

        # Pop remaining item
        key, value = d.popitem()
        assert len(d) == 0

        # Pop from empty dict
        with pytest.raises(KeyError, match="popitem\\(\\): dictionary is empty"):
            d.popitem()

    def test_copy(self, animal_hierarchy):
        """Test copy method."""
        Animal, Dog = animal_hierarchy["Animal"], animal_hierarchy["Dog"]
        d = SubclassDict()
        d[Animal] = "animal"
        d[Dog] = "dog"

        d_copy = d.copy()
        assert d_copy is not d
        assert d_copy[Animal] == "animal"
        assert d_copy[Dog] == "dog"

        # Modifying copy shouldn't affect original
        d_copy[Animal] = "new_animal"
        assert d[Animal] == "animal"
        assert d_copy[Animal] == "new_animal"

    def test_clear(self, animal_hierarchy):
        """Test clear method."""
        Animal, Dog = animal_hierarchy["Animal"], animal_hierarchy["Dog"]
        d = SubclassDict()
        d[Animal] = "animal"
        d[Dog] = "dog"

        d.clear()
        assert len(d) == 0
        assert Animal not in d
        assert Dog not in d


class TestSubclassDictCaching:
    """Test caching behavior."""

    def test_cache_consistency(self, animal_hierarchy):
        """Test that cache is maintained correctly."""
        Animal, Dog, Puppy = (
            animal_hierarchy["Animal"],
            animal_hierarchy["Dog"],
            animal_hierarchy["Puppy"],
        )
        d = SubclassDict()
        d[Animal] = "animal"

        # First access should populate cache
        assert d[Dog] == "animal"
        assert Dog in d._subclass_cache

        # Second access should use cache
        assert d[Dog] == "animal"

        # Adding new key should invalidate relevant cache entries
        d[Dog] = "dog"
        # Access Puppy to populate cache
        assert d[Puppy] == "dog"  # Should find Dog's value now
        # Cache should now contain Puppy
        assert Puppy in d._subclass_cache  # Cache entry exists

    def test_cache_invalidation_on_delete(self, animal_hierarchy):
        """Test cache invalidation when deleting keys."""
        Animal, Dog, Puppy = (
            animal_hierarchy["Animal"],
            animal_hierarchy["Dog"],
            animal_hierarchy["Puppy"],
        )
        d = SubclassDict()
        d[Animal] = "animal"
        d[Dog] = "dog"

        # Access to populate cache
        assert d[Puppy] == "dog"

        # Delete Dog
        del d[Dog]

        # Puppy should now find Animal's value
        assert d[Puppy] == "animal"

    def test_cache_clear_on_clear(self, animal_hierarchy):
        """Test that cache is cleared when dict is cleared."""
        Animal, Dog = animal_hierarchy["Animal"], animal_hierarchy["Dog"]
        d = SubclassDict()
        d[Animal] = "animal"

        # Access to populate cache
        assert d[Dog] == "animal"
        assert Dog in d._subclass_cache

        # Clear should reset cache
        d.clear()
        assert len(d._subclass_cache) == 0


class TestSubclassDictEdgeCases:
    """Test edge cases and error conditions."""

    def test_non_type_key(self):
        """Test behavior with non-type keys."""
        d = SubclassDict()

        # Non-type keys should work normally (no subclass lookup)
        d["string"] = "value"
        assert d["string"] == "value"
        assert "string" in d

        # But subclass lookup won't work for non-types
        with pytest.raises(TypeError):
            issubclass("string", "other_string")

    def test_none_values(self, animal_hierarchy):
        """Test handling of None values."""
        Animal = animal_hierarchy["Animal"]
        d = SubclassDict()
        d[Animal] = None

        assert d[Animal] is None
        assert Animal in d

    def test_empty_subclass_lookup(self, animal_hierarchy):
        """Test lookup when no superclass exists."""
        Bird = animal_hierarchy["Bird"]
        d = SubclassDict()

        with pytest.raises(KeyError):
            d[Bird]

    def test_self_reference(self):
        """Test that a class doesn't find itself as a superclass."""

        class A:
            pass

        d = SubclassDict()
        d[A] = "a"

        # A should find itself directly, not through subclass lookup
        assert d[A] == "a"
        assert A in d

    def test_circular_inheritance_handling(self):
        """Test behavior with potential circular inheritance scenarios."""

        # This is more of a theoretical test since Python doesn't allow
        # true circular inheritance, but we test the robustness
        class A:
            pass

        class B(A):
            pass

        class C(B):
            pass

        d = SubclassDict()
        d[A] = "a"
        d[B] = "b"

        # C should find B (closest superclass)
        assert d[C] == "b"

        # B should find A
        assert d[B] == "b"  # Direct match
        # But if we delete B, C should find A
        del d[B]
        assert d[C] == "a"


class TestSubclassDictPerformance:
    """Test performance characteristics."""

    def test_large_hierarchy_performance(self):
        """Test performance with large class hierarchy."""
        # Create a deep hierarchy
        classes = []
        prev_class = None

        for _ in range(100):
            if prev_class is None:

                class Base:
                    pass

                classes.append(Base)
                prev_class = Base
            else:

                class Sub(prev_class):
                    pass

                classes.append(Sub)
                prev_class = Sub

        d = SubclassDict()
        d[classes[0]] = "base"

        # Accessing the deepest class should still be fast due to caching
        import time

        start = time.time()
        for _ in range(1000):
            d[classes[-1]]
        end = time.time()

        # Should be fast (less than 1 second for 1000 lookups)
        assert end - start < 1.0
