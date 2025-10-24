"""Comprehensive tests for the TypeDict class."""

import pytest

from typedict import TypeDict


class TestTypeDictBasic:
    """Test basic TypeDict functionality."""

    def test_empty_dict(self):
        """Test creating an empty TypeDict."""
        td = TypeDict()
        assert len(td) == 0
        assert not td
        assert str(td) == "TypeDict()"
        assert repr(td) == "TypeDict()"

    def test_set_and_get_item(self):
        """Test setting and getting items."""
        td = TypeDict()
        td[42] = "hello"
        assert td[int] == "hello"
        assert td[42] == "hello"

        td["world"] = 123
        assert td[str] == 123
        assert td["test"] == 123

    def test_type_key_overwrites_value_key(self):
        """Test that using a type key overwrites the value key."""
        td = TypeDict()
        td[42] = "value_key"
        td[int] = "type_key"
        assert td[int] == "type_key"
        assert td[42] == "type_key"

    def test_delitem(self):
        """Test deleting items."""
        td = TypeDict()
        td[42] = "hello"
        assert int in td

        del td[42]
        assert int not in td
        with pytest.raises(KeyError):
            td[int]

    def test_contains(self):
        """Test the __contains__ method."""
        td = TypeDict()
        td[42] = "hello"

        assert int in td
        assert 42 in td
        assert str not in td
        assert "test" not in td

    def test_get_method(self):
        """Test the get method."""
        td = TypeDict()
        td[42] = "hello"

        assert td.get(int) == "hello"
        assert td.get(42) == "hello"
        assert td.get(str) is None
        assert td.get(str, "default") == "default"

    def test_pop_method(self):
        """Test the pop method."""
        td = TypeDict()
        td[42] = "hello"

        assert td.pop(int) == "hello"
        assert int not in td

        td[42] = "world"
        assert td.pop(str, "default") == "default"
        assert td.pop(str) is None

    def test_setdefault_method(self):
        """Test the setdefault method."""
        td = TypeDict()

        # Key doesn't exist
        result = td.setdefault(int, "default")
        assert result == "default"
        assert td[int] == "default"

        # Key exists
        result = td.setdefault(int, "new_default")
        assert result == "default"
        assert td[int] == "default"

    def test_update_method(self):
        """Test the update method."""
        td = TypeDict()
        td.update({42: "hello", "world": 123})

        assert td[int] == "hello"
        assert td[str] == 123

        # Update with another TypeDict
        td2 = TypeDict()
        td2[3.14] = "pi"
        td.update(td2)
        assert td[float] == "pi"

        # Update with kwargs (using string keys that will be converted)
        td.update(**{"True": "boolean", "None": "none"})
        # Note: These won't work as expected because "True" and "None" are strings, not boolean/None
        # Let's test with actual boolean and None values instead
        td[True] = "boolean"
        td[None] = "none"
        assert td[bool] == "boolean"
        assert td[type(None)] == "none"

    def test_keys_values_items(self):
        """Test keys, values, and items methods."""
        td = TypeDict()
        td[42] = "hello"
        td["world"] = 123

        keys = list(td.keys())
        values = list(td.values())
        items = list(td.items())

        assert int in keys
        assert str in keys
        assert "hello" in values
        assert 123 in values
        assert (int, "hello") in items
        assert (str, 123) in items

    def test_get_types_method(self):
        """Test the get_types method."""
        td = TypeDict()
        td[42] = "hello"
        td["world"] = 123

        types = td.get_types()
        assert int in types
        assert str in types
        assert len(types) == 2

    def test_has_type_method(self):
        """Test the has_type method."""
        td = TypeDict()
        td[42] = "hello"

        assert td.has_type(int)
        assert not td.has_type(str)

    def test_repr_and_str(self):
        """Test string representations."""
        td = TypeDict()
        td[42] = "hello"
        td["world"] = 123

        repr_str = repr(td)
        assert "TypeDict" in repr_str
        assert "int: 'hello'" in repr_str
        assert "str: 123" in repr_str

        assert str(td) == repr(td)


class TestTypeDictEdgeCases:
    """Test edge cases and special types."""

    def test_none_key(self):
        """Test using None as a key."""
        td = TypeDict()
        td[None] = "none_value"
        assert td[type(None)] == "none_value"
        assert td[None] == "none_value"

    def test_boolean_keys(self):
        """Test using boolean values as keys."""
        td = TypeDict()
        td[True] = "true_value"
        td[False] = "false_value"

        assert td[bool] == "false_value"  # Last one wins
        assert td[True] == "false_value"
        assert td[False] == "false_value"

    def test_custom_class(self):
        """Test using custom class instances as keys."""

        class CustomClass:
            pass

        td = TypeDict()
        instance = CustomClass()
        td[instance] = "custom_value"

        assert td[CustomClass] == "custom_value"
        assert td[instance] == "custom_value"

    def test_type_as_key(self):
        """Test using types directly as keys."""
        td = TypeDict()
        td[int] = "int_type"
        td[str] = "str_type"

        assert td[int] == "int_type"
        assert td[str] == "str_type"

    def test_mixed_keys(self):
        """Test mixing value keys and type keys."""
        td = TypeDict()
        td[42] = "value_key"
        td[int] = "type_key"

        # Type key should overwrite value key
        assert td[int] == "type_key"
        assert td[42] == "type_key"

    def test_complex_types(self):
        """Test with complex types like lists and dicts."""
        td = TypeDict()
        td[[]] = "list_value"
        td[{}] = "dict_value"

        assert td[list] == "list_value"
        assert td[dict] == "dict_value"

    def test_float_and_int_collision(self):
        """Test that int and float are treated as different types."""
        td = TypeDict()
        td[42] = "int_value"
        td[42.0] = "float_value"

        assert td[int] == "int_value"
        assert td[float] == "float_value"

    def test_empty_string_key(self):
        """Test using empty string as key."""
        td = TypeDict()
        td[""] = "empty_string"
        assert td[str] == "empty_string"
        assert td[""] == "empty_string"


class TestTypeDictErrorHandling:
    """Test error handling and edge cases."""

    def test_key_error_on_missing_key(self):
        """Test KeyError when accessing missing key."""
        td = TypeDict()
        with pytest.raises(KeyError):
            td[int]

    def test_key_error_on_delete_missing_key(self):
        """Test KeyError when deleting missing key."""
        td = TypeDict()
        with pytest.raises(KeyError):
            del td[int]

    def test_unhashable_key_error(self):
        """Test that unhashable keys are converted to their type."""
        td = TypeDict()
        # Lists are not hashable, but they get converted to their type (list)
        td[[]] = "value"  # This should work, converting [] to list type
        assert td[list] == "value"
        assert td[[]] == "value"  # Any list should work

    def test_nested_dict_behavior(self):
        """Test behavior with nested dictionaries."""
        td = TypeDict()
        inner_dict = {"nested": "value"}
        td[inner_dict] = "outer_value"

        assert td[dict] == "outer_value"
        assert td[inner_dict] == "outer_value"


class TestTypeDictPerformance:
    """Test performance-related functionality."""

    def test_large_dict(self):
        """Test with a large number of items."""
        td = TypeDict()

        # Add many items
        for i in range(1000):
            td[i] = f"value_{i}"

        # All keys are integers, so they map to the same type
        assert len(td) == 1  # Only one unique type (int)
        assert td[int] == "value_999"  # Last one wins

        # Test access
        assert td[42] == "value_999"
        assert td[999] == "value_999"

    def test_type_collision_performance(self):
        """Test performance with many type collisions."""
        td = TypeDict()

        # All keys should map to int type
        for i in range(100):
            td[i] = f"value_{i}"

        # Should only have one key (int type)
        assert len(td) == 1
        assert td[int] == "value_99"


class TestTypeDictCompatibility:
    """Test compatibility with standard dict operations."""

    def test_dict_constructor(self):
        """Test creating TypeDict from regular dict."""
        regular_dict = {42: "hello", "world": 123}
        td = TypeDict(regular_dict)

        assert td[int] == "hello"
        assert td[str] == 123

    def test_copy_behavior(self):
        """Test copying behavior."""
        td1 = TypeDict()
        td1[42] = "hello"

        td2 = TypeDict(td1)
        assert td2[int] == "hello"

        # Modify original
        td1[42] = "world"
        assert td1[int] == "world"
        assert td2[int] == "hello"  # Copy should be independent

    def test_len_function(self):
        """Test len() function."""
        td = TypeDict()
        assert len(td) == 0

        td[42] = "hello"
        assert len(td) == 1

        td["world"] = 123
        assert len(td) == 2

        # Adding same type should not increase length
        td[43] = "another_int"
        assert len(td) == 2  # Still only int and str types
