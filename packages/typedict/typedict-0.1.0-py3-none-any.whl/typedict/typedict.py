"""A dictionary that uses types as keys, automatically converting values to their types."""

from collections import UserDict
from collections.abc import Hashable, ItemsView, KeysView, ValuesView
from typing import Any, TypeVar

T = TypeVar("T")


class TypeDict(UserDict[type, Any]):
    """
    A dictionary that uses types as keys.

    When you set a value with a key, the key is automatically converted to its type.
    For example:
        td = TypeDict()
        td[42] = "hello"  # Key becomes int, not 42
        td[int] = "world"  # Key is already int
        print(td[int])     # "world" (the last value set for int type)

    This is useful for storing values by type, where you want to access them
    using the type rather than the specific instance.
    """

    def __getitem__(self, key: Hashable) -> Any:
        """Get the value for the given key, converting the key to its type first."""
        _key = _gettype(key)
        return self.data[_key]

    def __setitem__(self, key: Hashable, value: Any) -> None:
        """Set the value for the given key, converting the key to its type first."""
        try:
            _key = _gettype(key)
        except TypeError as e:
            # If the key is not hashable, raise TypeError
            raise TypeError(f"unhashable type: '{type(key).__name__}'") from e
        self.data[_key] = value

    def __delitem__(self, key: Hashable) -> None:
        """Delete the value for the given key, converting the key to its type first."""
        _key = _gettype(key)
        del self.data[_key]

    def __contains__(self, key: Hashable) -> bool:
        """Check if the given key (converted to its type) exists in the dictionary."""
        _key = _gettype(key)
        return _key in self.data

    def get(self, key: Hashable, default: Any = None) -> Any:
        """Get the value for the given key, returning default if key doesn't exist."""
        _key = _gettype(key)
        return self.data.get(_key, default)

    def pop(self, key: Hashable, default: Any = None) -> Any:
        """Remove and return the value for the given key, returning default if key doesn't exist."""
        _key = _gettype(key)
        return self.data.pop(_key, default)

    def setdefault(self, key: Hashable, default: Any = None) -> Any:
        """Set the value for the given key to default if key doesn't exist, return the value."""
        _key = _gettype(key)
        return self.data.setdefault(_key, default)

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Update the dictionary with values from other dict or keyword arguments."""
        if args:
            other = args[0]
            if isinstance(other, TypeDict):
                self.data.update(other.data)
            else:
                for key, value in other.items():
                    self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    def keys(self) -> KeysView[type]:
        """Return a view of the type keys in the dictionary."""
        return self.data.keys()

    def values(self) -> ValuesView[Any]:
        """Return a view of the values in the dictionary."""
        return self.data.values()

    def items(self) -> ItemsView[type, Any]:
        """Return a view of the (type, value) pairs in the dictionary."""
        return self.data.items()

    def get_types(self) -> list[type]:
        """Return a list of all types used as keys in the dictionary."""
        return list(self.data.keys())

    def has_type(self, type_key: type) -> bool:
        """Check if the given type exists as a key in the dictionary."""
        return type_key in self.data

    def __repr__(self) -> str:
        """Return a string representation of the TypeDict."""
        if not self.data:
            return "TypeDict()"
        items = [f"{k.__name__}: {repr(v)}" for k, v in self.data.items()]
        return f"TypeDict({{{', '.join(items)}}})"

    def __str__(self) -> str:
        """Return a string representation of the TypeDict."""
        return self.__repr__()


def _gettype(value: Any) -> type:
    """
    Get the type of a value.

    Args:
        value: The value to get the type of

    Returns:
        The type of the value. If value is already a type, returns it directly.
        Otherwise, returns type(value).
    """
    if isinstance(value, type):
        return value
    else:
        return type(value)
