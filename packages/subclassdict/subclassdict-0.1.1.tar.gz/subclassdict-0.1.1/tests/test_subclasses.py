"""Tests for subclasses utility function."""

from subclassdict import subclasses


class TestSubclasses:
    """Test subclasses utility function."""

    def test_no_subclasses(self):
        """Test with class that has no subclasses."""

        class A:
            pass

        result = subclasses(A)
        assert result == []

    def test_single_level_subclasses(self):
        """Test with single level of subclasses."""

        class A:
            pass

        class B(A):
            pass

        class C(A):
            pass

        result = subclasses(A)
        assert len(result) == 2
        assert B in result
        assert C in result

    def test_multiple_levels_subclasses(self):
        """Test with multiple levels of subclasses."""

        class A:
            pass

        class B(A):
            pass

        class C(A):
            pass

        class D(B):
            pass

        class E(B):
            pass

        class F(C):
            pass

        result = subclasses(A)
        assert len(result) == 5
        assert B in result
        assert C in result
        assert D in result
        assert E in result
        assert F in result

    def test_deep_hierarchy(self):
        """Test with deep class hierarchy."""

        class A:
            pass

        class B(A):
            pass

        class C(B):
            pass

        class D(C):
            pass

        class E(D):
            pass

        result = subclasses(A)
        assert len(result) == 4
        assert B in result
        assert C in result
        assert D in result
        assert E in result

    def test_multiple_inheritance(self):
        """Test with multiple inheritance."""

        class A:
            pass

        class B:
            pass

        class C(A, B):
            pass

        class D(C):
            pass

        # Test subclasses of A
        result_a = subclasses(A)
        assert len(result_a) == 2
        assert C in result_a
        assert D in result_a

        # Test subclasses of B
        result_b = subclasses(B)
        assert len(result_b) == 2
        assert C in result_b
        assert D in result_b

        # Test subclasses of C
        result_c = subclasses(C)
        assert len(result_c) == 1
        assert D in result_c

    def test_complex_hierarchy(self):
        """Test with complex hierarchy."""

        class Animal:
            pass

        class Mammal(Animal):
            pass

        class Bird(Animal):
            pass

        class Dog(Mammal):
            pass

        class Cat(Mammal):
            pass

        class Puppy(Dog):
            pass

        class Kitten(Cat):
            pass

        class Eagle(Bird):
            pass

        # Test Animal subclasses
        animal_subclasses = subclasses(Animal)
        # Should have 7 subclasses: Mammal, Bird, Dog, Cat, Puppy, Kitten, Eagle
        assert len(animal_subclasses) == 7
        assert Mammal in animal_subclasses
        assert Bird in animal_subclasses
        assert Dog in animal_subclasses
        assert Cat in animal_subclasses
        assert Puppy in animal_subclasses
        assert Kitten in animal_subclasses
        assert Eagle in animal_subclasses

        # Test Mammal subclasses
        mammal_subclasses = subclasses(Mammal)
        assert len(mammal_subclasses) == 4
        assert Dog in mammal_subclasses
        assert Cat in mammal_subclasses
        assert Puppy in mammal_subclasses
        assert Kitten in mammal_subclasses

        # Test Dog subclasses
        dog_subclasses = subclasses(Dog)
        assert len(dog_subclasses) == 1
        assert Puppy in dog_subclasses

    def test_empty_hierarchy(self):
        """Test with classes that have no subclasses."""

        class A:
            pass

        class B:
            pass

        assert subclasses(A) == []
        assert subclasses(B) == []

    def test_single_subclass(self):
        """Test with single subclass."""

        class A:
            pass

        class B(A):
            pass

        result = subclasses(A)
        assert len(result) == 1
        assert B in result

    def test_builtin_types(self):
        """Test with built-in types (if they have subclasses)."""
        # Most built-in types don't have subclasses in the traditional sense,
        # but we can test the function doesn't crash
        try:
            result = subclasses(int)
            # Should return a list (might be empty)
            assert isinstance(result, list)
        except (TypeError, AttributeError):
            # Some built-in types might not support __subclasses__
            pass

    def test_return_type(self):
        """Test that function returns correct type."""

        class A:
            pass

        class B(A):
            pass

        result = subclasses(A)
        assert isinstance(result, list)
        assert all(isinstance(cls, type) for cls in result)
