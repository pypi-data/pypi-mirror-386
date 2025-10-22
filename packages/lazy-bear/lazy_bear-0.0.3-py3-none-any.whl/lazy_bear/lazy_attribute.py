"""Module providing a lazy-loaded attribute wrapper."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from lazy_bear.lazy_imports import LazyLoader


class LazyAttr:
    """A lazy-loaded attribute from a LazyLoader module."""

    __slots__: tuple = ("_attr_name", "_cached_attr", "_loader")

    def __init__(self, n: str, loader: LazyLoader) -> None:  # pragma: no cover
        """Initialize a lazy-loaded attribute."""
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_attr_name", n)
        object.__setattr__(self, "_cached_attr", None)

    @property
    def _attr(self) -> Callable[..., Any]:  # pragma: no cover
        """Get the lazy-loaded attribute."""
        if self._cached_attr is None:
            self._cached_attr = getattr(self._loader._load(), self._attr_name)  # pyright: ignore[reportPrivateUsage]
        if self._cached_attr is None:
            raise AttributeError(f"Attribute '{self._attr_name}' not found in module '{self._loader._module_name}'")
        return self._cached_attr

    @property
    def value(self) -> Any:  # pragma: no cover
        """Get the lazy-loaded attribute value."""
        return self._attr

    def unwrap(self) -> Any:  # pragma: no cover
        """Get the lazy-loaded attribute value."""
        return self._attr

    def __call__(self, *args, **kwargs) -> Any:
        """Call the lazy-loaded attribute if it is callable."""
        target: Callable[..., Any] = self._attr
        if not callable(target):
            raise TypeError(f"Attribute '{self._attr_name}' is not callable.")
        return target(*args, **kwargs)

    def __setattr__(self, name: str, value: Any) -> None:  # pragma: no cover
        if name in self.__slots__:
            super().__setattr__(name, value)
        if self._cached_attr is None:
            raise AttributeError(f"Cannot set attribute '{name}' before '{self._attr_name}' is loaded.")
        setattr(self._attr, name, value)

    def __contains__(self, item: object) -> bool:  # pragma: no cover
        if not hasattr(self._attr, "__contains__"):
            raise TypeError(f"Attribute '{self._attr_name}' does not support membership testing.")
        return item in self._attr  # type: ignore[operator]

    def __setitem__(self, key: str, value: Any) -> None:  # pragma: no cover
        if not hasattr(self._attr, "__setitem__"):
            raise TypeError(f"Attribute '{self._attr_name}' does not support item assignment.")
        self._attr[key] = value  # type: ignore[index]

    def __getitem__(self, key: str) -> Any:  # pragma: no cover
        if not hasattr(self._attr, "__getitem__"):
            raise TypeError(f"Attribute '{self._attr_name}' does not support item access.")
        return self._attr[key]  # type: ignore[index]

    def __iter__(self):  # pragma: no cover
        if not hasattr(self._attr, "__iter__"):
            raise TypeError(f"Attribute '{self._attr_name}' is not iterable.")
        return iter(self._attr)  # type: ignore[return-value]

    def __len__(self) -> int:  # pragma: no cover
        if not hasattr(self._attr, "__len__"):
            raise TypeError(f"Attribute '{self._attr_name}' does not have length.")
        return len(self._attr)  # type: ignore[return-value]

    def __getattr__(self, name: str) -> Any:  # pragma: no cover
        if not hasattr(self._attr, name):
            return self._attr  # type: ignore[reportGeneralTypeIssues]
        return getattr(self._attr, name)

    def __or__(self, other: Any) -> Any:  # pragma: no cover
        if not hasattr(self._attr, "__or__"):
            raise TypeError(f"Attribute '{self._attr_name}' does not support the '|' operator.")
        return self._attr | other  # type: ignore[operator]

    def __ror__(self, other: Any) -> Any:  # pragma: no cover
        if not hasattr(self._attr, "__ror__"):
            raise TypeError(f"Attribute '{self._attr_name}' does not support the '|' operator.")
        return other | self._attr  # type: ignore[operator]

    def __dir__(self) -> list[str]:  # pragma: no cover
        """List the attributes of the lazy-loaded attribute.

        This will trigger the loading of the attribute if it hasn't been loaded yet.
        """
        return dir(self._attr)

    def __repr__(self) -> str:  # pragma: no cover
        if self._cached_attr is None:
            return f"<lazy attribute '{self._attr_name}' from module '{self._loader._name}' (Not loaded yet)>"  # pyright: ignore[reportPrivateUsage]
        return repr(self._cached_attr)


__all__ = ["LazyAttr"]
