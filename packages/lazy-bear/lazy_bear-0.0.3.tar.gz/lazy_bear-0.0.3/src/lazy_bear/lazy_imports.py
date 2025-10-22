"""A set of helper functions for dynamic module loading."""

import importlib
import sys
from threading import RLock
from types import ModuleType
from typing import Any, ClassVar

from lazy_bear.lazy_attribute import LazyAttr

_lock = RLock()


def get_calling_file(d: int = 2) -> str:
    """Get the filename of the calling frame.

    Args:
        d (int): The depth of the frame to inspect. Default is 2.
    """
    return sys._getframe(d).f_code.co_filename  # type: ignore[attr-defined]


def get_calling_globals(d: int = 2) -> dict[str, Any]:
    """Get the globals of the calling frame.

    Args:
        d (int): The depth of the frame to inspect. Default is 2.
    """
    return sys._getframe(d).f_globals  # type: ignore[attr-defined]


class LazyLoader(ModuleType):
    """Class for module lazy loading."""

    _globals_modules: ClassVar[dict[str, dict[str, ModuleType]]] = {}
    __slots__: tuple = ("_module", "_name", "_parent_globals")

    @classmethod
    def clear_globals(cls) -> None:
        """Clear the stored globals modules mapping."""
        with _lock:
            cls._globals_modules.clear()

    @classmethod
    def init(cls, f: str) -> dict[str, ModuleType]:  # pragma: no cover
        """Initialize the LazyLoader for a given file and its parent's globals.

        Args:
            f (str): The file path of the calling module.

        Returns:
            dict[str, ModuleType]: The globals of the calling module.
        """
        with _lock:
            if f not in cls._globals_modules:
                cls._globals_modules[f] = get_calling_globals()
            return cls._globals_modules[f]

    def __init__(self, name: str) -> None:
        """Initialize the LazyLoader.

        Args:
            name (str): The full name of the module to load, must be the full path.
        """
        self._name: str = name
        self._parent_globals: dict[str, ModuleType] = self.init(get_calling_file())
        self._module = None
        super().__init__(str(name))

    def _load(self) -> ModuleType:
        """Load the module and insert it into the parent's globals."""
        if self._module:
            return self._module
        module: ModuleType = importlib.import_module(self.__name__)
        self._parent_globals[self._name] = module
        sys.modules[self._name] = module
        self.__dict__.update(module.__dict__)
        self._module = module
        return module

    def to(self, n: str) -> LazyAttr:  # pyright: ignore[reportInvalidTypeVarUse]
        """Get a lazy attribute from the module.

        Args:
            n (str): The name of the attribute to get.

        Returns:
            Any: The attribute from the module.
        """
        return LazyAttr(n, self)

    def to_many(self, *names: str) -> tuple[LazyAttr, ...]:
        """Get multiple lazy attributes from the module.

        Args:
            *names (str): The names of the attributes to get.

        Returns:
            tuple[LazyAttr, ...]: The attributes from the module.
        """
        return tuple(LazyAttr(n, self) for n in names)

    def __getattr__(self, item: str) -> Any:
        module: ModuleType = self._load()
        return getattr(module, item)

    def __dir__(self) -> list[str]:
        module: ModuleType = self._load()
        return dir(module)

    def __repr__(self) -> str:
        if not self._module:
            return f"<module '{self.__name__} (Not loaded yet)'>"
        return repr(self._module)


def lazy(n: str) -> LazyLoader:
    """Lazily load a module by its full name.

    Args:
        n (str): The full name of the module to load.

    Returns:
        ModuleType: The loaded module.

    Raises:
        ImportError: If the module cannot be found or loaded.
    """
    return LazyLoader(n)


__all__ = ["LazyLoader", "lazy"]
