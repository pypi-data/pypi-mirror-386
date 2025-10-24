"""Integration tests for real-world usage scenarios."""

import pytest

from subclassdict import SubclassDict, subclasses


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_plugin_system(self):
        """Test using SubclassDict for a plugin system."""

        class Plugin:
            def __init__(self, name: str):
                self.name = name

        class DatabasePlugin(Plugin):
            pass

        class WebPlugin(Plugin):
            pass

        class APIPlugin(WebPlugin):
            pass

        # Register plugins
        plugins = SubclassDict()
        plugins[Plugin] = "base_plugin"
        plugins[DatabasePlugin] = "database_plugin"
        plugins[WebPlugin] = "web_plugin"

        # Test plugin resolution
        assert plugins[DatabasePlugin] == "database_plugin"
        assert plugins[APIPlugin] == "web_plugin"  # Finds WebPlugin
        assert plugins[Plugin] == "base_plugin"

    def test_event_handling_system(self):
        """Test using SubclassDict for event handling."""

        class Event:
            def __init__(self, name: str):
                self.name = name

        class UserEvent(Event):
            pass

        class LoginEvent(UserEvent):
            pass

        class LogoutEvent(UserEvent):
            pass

        class SystemEvent(Event):
            pass

        class ErrorEvent(SystemEvent):
            pass

        # Register event handlers
        handlers = SubclassDict()
        handlers[Event] = "generic_handler"
        handlers[UserEvent] = "user_handler"
        handlers[SystemEvent] = "system_handler"

        # Test event handling
        assert handlers[LoginEvent] == "user_handler"
        assert handlers[LogoutEvent] == "user_handler"
        assert handlers[ErrorEvent] == "system_handler"
        assert handlers[Event] == "generic_handler"

    def test_serialization_system(self):
        """Test using SubclassDict for serialization."""

        class Serializable:
            def serialize(self):
                pass

        class JSONSerializable(Serializable):
            pass

        class XMLSerializable(Serializable):
            pass

        class YAMLSerializable(Serializable):
            pass

        class JSONAPISerializable(JSONSerializable):
            pass

        # Register serializers
        serializers = SubclassDict()
        serializers[Serializable] = "generic_serializer"
        serializers[JSONSerializable] = "json_serializer"
        serializers[XMLSerializable] = "xml_serializer"
        serializers[YAMLSerializable] = "yaml_serializer"

        # Test serialization
        assert serializers[JSONAPISerializable] == "json_serializer"
        assert serializers[JSONSerializable] == "json_serializer"
        assert serializers[XMLSerializable] == "xml_serializer"
        assert serializers[YAMLSerializable] == "yaml_serializer"
        assert serializers[Serializable] == "generic_serializer"

    def test_validation_system(self):
        """Test using SubclassDict for validation."""

        class Validator:
            def validate(self, value):
                pass

        class StringValidator(Validator):
            pass

        class NumberValidator(Validator):
            pass

        class EmailValidator(StringValidator):
            pass

        class PhoneValidator(StringValidator):
            pass

        # Register validators
        validators = SubclassDict()
        validators[Validator] = "generic_validator"
        validators[StringValidator] = "string_validator"
        validators[NumberValidator] = "number_validator"

        # Test validation
        assert validators[EmailValidator] == "string_validator"
        assert validators[PhoneValidator] == "string_validator"
        assert validators[StringValidator] == "string_validator"
        assert validators[NumberValidator] == "number_validator"
        assert validators[Validator] == "generic_validator"

    def test_factory_pattern(self):
        """Test using SubclassDict for factory pattern."""

        class Product:
            def __init__(self, name: str):
                self.name = name

        class Electronics(Product):
            pass

        class Clothing(Product):
            pass

        class Laptop(Electronics):
            pass

        class Shirt(Clothing):
            pass

        # Register factories
        factories = SubclassDict()
        factories[Product] = "generic_factory"
        factories[Electronics] = "electronics_factory"
        factories[Clothing] = "clothing_factory"

        # Test factory selection
        assert factories[Laptop] == "electronics_factory"
        assert factories[Shirt] == "clothing_factory"
        assert factories[Electronics] == "electronics_factory"
        assert factories[Clothing] == "clothing_factory"
        assert factories[Product] == "generic_factory"

    def test_combined_with_subclasses_function(self):
        """Test combining SubclassDict with subclasses function."""

        class BaseHandler:
            def handle(self):
                pass

        class HTTPHandler(BaseHandler):
            pass

        class HTTPSHandler(HTTPHandler):
            pass

        class FTPHandler(BaseHandler):
            pass

        class SFTPHandler(FTPHandler):
            pass

        # Get all subclasses of BaseHandler
        all_handlers = subclasses(BaseHandler)
        assert len(all_handlers) == 4
        assert HTTPHandler in all_handlers
        assert HTTPSHandler in all_handlers
        assert FTPHandler in all_handlers
        assert SFTPHandler in all_handlers

        # Use SubclassDict for handler registration
        handlers = SubclassDict()
        handlers[BaseHandler] = "base_handler"
        handlers[HTTPHandler] = "http_handler"
        handlers[FTPHandler] = "ftp_handler"

        # Test handler resolution
        assert handlers[HTTPSHandler] == "http_handler"
        assert handlers[SFTPHandler] == "ftp_handler"
        assert handlers[HTTPHandler] == "http_handler"
        assert handlers[FTPHandler] == "ftp_handler"
        assert handlers[BaseHandler] == "base_handler"

    def test_dynamic_class_registration(self):
        """Test dynamic class registration and lookup."""
        # Create classes dynamically
        Base = type("Base", (), {})
        Derived1 = type("Derived1", (Base,), {})
        Derived2 = type("Derived2", (Base,), {})
        DeepDerived = type("DeepDerived", (Derived1,), {})

        # Register in SubclassDict
        registry = SubclassDict()
        registry[Base] = "base"
        registry[Derived1] = "derived1"

        # Test lookups
        assert registry[Base] == "base"
        assert registry[Derived1] == "derived1"
        assert registry[Derived2] == "base"  # Falls back to Base
        assert registry[DeepDerived] == "derived1"  # Finds Derived1

    def test_performance_with_large_hierarchy(self):
        """Test performance with large class hierarchy."""
        # Create a large hierarchy
        classes = []
        prev_class = None

        for i in range(50):
            if prev_class is None:
                new_class = type(f"Class{i}", (), {})
            else:
                new_class = type(f"Class{i}", (prev_class,), {})
            classes.append(new_class)
            prev_class = new_class

        # Register some values
        registry = SubclassDict()
        registry[classes[0]] = "root"
        registry[classes[10]] = "level10"
        registry[classes[25]] = "level25"

        # Test lookups at different levels
        assert registry[classes[0]] == "root"
        assert registry[classes[5]] == "root"  # Should find root
        assert registry[classes[15]] == "level10"  # Should find level10
        assert registry[classes[30]] == "level25"  # Should find level25
        assert registry[classes[49]] == "level25"  # Should find level25

    def test_error_handling_scenarios(self):
        """Test error handling in real-world scenarios."""

        class Base:
            pass

        class Derived(Base):
            pass

        class Unrelated:
            pass

        registry = SubclassDict()
        registry[Base] = "base"

        # Valid lookups
        assert registry[Base] == "base"
        assert registry[Derived] == "base"

        # Invalid lookups should raise KeyError
        with pytest.raises(KeyError):
            registry[Unrelated]

        # Test with get method for safe lookups
        assert registry.get(Derived) == "base"
        assert registry.get(Unrelated) is None
        assert registry.get(Unrelated, "default") == "default"

        # Test with contains for safe checking
        assert Base in registry
        assert Derived in registry
        assert Unrelated not in registry
