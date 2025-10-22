import sys

from lazy_bear.lazy_attribute import LazyAttr
from lazy_bear.lazy_imports import LazyLoader


def get_module(n: str) -> LazyLoader:
    sys.modules.pop(n, None)
    LazyLoader.clear_globals()
    return LazyLoader(n)


def test_lazy_attr_dir() -> None:
    """Test LazyAttr __dir__ functionality."""
    test_module = "math"
    lazy_loader = get_module(test_module)
    lazy_attr = LazyAttr("sqrt", lazy_loader)
    dir_result: list[str] = dir(lazy_attr)
    assert isinstance(dir_result, list)
    assert "Not loaded yet" not in dir_result


def test_lazy_attr_repr() -> None:
    """Test LazyAttr __repr__ functionality."""
    test_module = "math"
    lazy_loader = get_module(test_module)
    sqrt = LazyAttr("sqrt", lazy_loader)
    repr_result: str = repr(sqrt)
    assert isinstance(repr_result, str)
    sqrt_result = sqrt(25)
    assert sqrt_result == 5.0


def test_lazy_attr_contains() -> None:
    """Test LazyAttr __contains__ functionality."""
    test_module = "os"
    lazy_loader = get_module(test_module)
    environ = LazyAttr("environ", lazy_loader)
    environ["TEST_KEY"] = "TEST_VALUE"
    assert environ.__setitem__("TEST_KEY", "TEST_VALUE") is None
    assert environ.__contains__("TEST_KEY")
    assert environ.__getitem__("TEST_KEY") == "TEST_VALUE"
    assert environ.__len__() > 0
    assert environ.__iter__() is not None
    assert len(environ) > 0
    assert "TEST_KEY" in environ
    assert "NON_EXISTENT_KEY" not in environ
    env_value = environ.value
    assert "<class 'os._Environ'>" in str(type(env_value))
    env_value = env_value.copy()
    assert isinstance(env_value, dict)
    assert env_value["TEST_KEY"] == "TEST_VALUE"


def test_lazy_attr() -> None:
    """Test LazyAttr functionality."""
    test_module = "math"
    math = get_module(test_module)
    sqrt = LazyAttr("sqrt", math)
    result = sqrt(16)
    assert result == 4.0
