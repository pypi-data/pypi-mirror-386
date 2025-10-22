from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import sys
from typing import TYPE_CHECKING

import pytest

from lazy_bear.lazy_imports import LazyAttr, LazyLoader, lazy


def get_module(n: str) -> LazyLoader:
    sys.modules.pop(n, None)
    LazyLoader.clear_globals()
    return LazyLoader(n)


def test_lazy_func() -> None:
    test_module = "random"
    sys.modules.pop(test_module, None)
    random: LazyLoader = lazy(test_module)
    assert test_module not in sys.modules
    value: int = random.randint(1, 10)
    assert 1 <= value <= 10
    assert test_module in sys.modules
    assert "Not loaded yet" not in repr(random)


def test_lazy_import() -> None:
    test_module = "json"
    json: LazyLoader = get_module(test_module)
    assert test_module not in sys.modules
    value: str = json.dumps({"key": "value"})
    assert test_module in sys.modules
    assert value == '{"key": "value"}'
    assert "Not loaded yet" not in repr(json)
    assert "dumps" in dir(json)


def test_lazy_import_repr() -> None:
    test_module = "math"
    math: LazyLoader = get_module(test_module)
    repr_before = repr(math)
    assert "Not loaded yet" in repr_before
    _ = math.sqrt(16)
    repr_after = repr(math)
    assert "Not loaded yet" not in repr_after


def test_dir() -> None:
    test_module = "collections"
    collections: LazyLoader = get_module(test_module)
    assert test_module not in sys.modules
    dir_test = dir(collections)  # calling this loads the module
    assert "Not loaded yet" not in repr(collections)
    assert "deque" in dir_test


def test_actually_lazy() -> None:
    test_module = "email.mime.text"
    loader: LazyLoader = get_module(test_module)
    assert test_module not in sys.modules
    _ = loader.MIMEText
    assert test_module in sys.modules


def test_fake_import() -> None:
    test_module = "non_existent_module_abcxyz"
    fake_module: LazyLoader = get_module(test_module)
    with pytest.raises(ModuleNotFoundError):
        _ = fake_module.some_attribute


def test_attr_access() -> None:
    test_module = "rich.console"

    if TYPE_CHECKING:
        from rich.console import Console  # noqa: PLC0415

        console: LazyLoader = get_module(test_module)
    else:
        console: LazyLoader = get_module(test_module)
        Console: LazyAttr = console.to("Console")  # lazy attribute  # noqa: N806

    # assert test_module not in sys.modules

    assert "Not loaded yet" in repr(console)
    assert "Not loaded yet" in repr(Console)

    console_instance = Console(width=100)
    assert test_module in sys.modules
    assert "console width=100" in repr(console_instance)
    buffer = StringIO()
    with redirect_stdout(buffer):
        console_instance.print("Hello, LazyLoader!")
    output: str = buffer.getvalue()
    assert "Hello, LazyLoader!" in output
    assert "Not loaded yet" not in repr(console)
    assert "Not loaded yet" not in repr(Console)


def test_multiple_attr_access() -> None:
    test_module = "math"
    math_loader: LazyLoader = get_module(test_module)
    if TYPE_CHECKING:
        from math import pow, sqrt  # noqa: A004, PLC0415

    sqrt, pow = math_loader.to_many("sqrt", "pow")

    assert test_module not in sys.modules
    assert "Not loaded yet" in repr(math_loader)
    assert "Not loaded yet" in repr(sqrt)
    assert "Not loaded yet" in repr(pow)

    sqrt_result = sqrt(25)
    pow_result = pow(2, 3)

    assert test_module in sys.modules
    assert sqrt_result == 5.0
    assert pow_result == 8
    assert "Not loaded yet" not in repr(math_loader)
    assert "Not loaded yet" not in repr(sqrt)
    assert "Not loaded yet" not in repr(pow)
