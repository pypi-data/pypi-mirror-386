from __future__ import annotations

from typing import Any
from typing_extensions import override

from ._proxy import LazyProxy


class ResourcesProxy(LazyProxy[Any]):
    """A proxy for the `autofix_bot.resources` module.

    This is used so that we can lazily import `autofix_bot.resources` only when
    needed *and* so that users can just import `autofix_bot` and reference `autofix_bot.resources`
    """

    @override
    def __load__(self) -> Any:
        import importlib

        mod = importlib.import_module("autofix_bot.resources")
        return mod


resources = ResourcesProxy().__as_proxied__()
