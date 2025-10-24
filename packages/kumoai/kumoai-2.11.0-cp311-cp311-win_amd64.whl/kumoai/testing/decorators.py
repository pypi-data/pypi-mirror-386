import importlib
import os
from typing import Callable

import packaging
from packaging.requirements import Requirement


def is_full_test() -> bool:
    r"""Whether to run the full but time-consuming test suite."""
    return os.getenv('FULL_TEST', '0') == '1'


def onlyFullTest(func: Callable) -> Callable:
    r"""A decorator to specify that this function belongs to the full test
    suite.
    """
    import pytest
    return pytest.mark.skipif(
        not is_full_test(),
        reason="Fast test run",
    )(func)


def has_package(package: str) -> bool:
    r"""Returns ``True`` in case ``package`` is installed."""
    req = Requirement(package)
    if importlib.util.find_spec(req.name) is None:
        return False

    try:
        module = importlib.import_module(req.name)
        if not hasattr(module, '__version__'):
            return True

        version = packaging.version.Version(module.__version__).base_version
        return version in req.specifier
    except Exception:
        return False


def withPackage(*args: str) -> Callable:
    r"""A decorator to skip tests if certain packages are not installed.
    Also supports version specification.
    """
    na_packages = {package for package in args if not has_package(package)}

    if len(na_packages) == 1:
        reason = f"Package '{list(na_packages)[0]}' not found"
    else:
        reason = f"Packages {na_packages} not found"

    def decorator(func: Callable) -> Callable:
        import pytest
        return pytest.mark.skipif(len(na_packages) > 0, reason=reason)(func)

    return decorator
