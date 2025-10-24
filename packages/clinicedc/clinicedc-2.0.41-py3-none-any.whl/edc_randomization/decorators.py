from typing import Any

from .exceptions import RegisterRandomizerError
from .randomizer import Randomizer
from .site_randomizers import site_randomizers

__all__ = ["register"]


def register(site=None, **kwargs) -> Any:
    """Registers a randomizer class."""
    site = site or site_randomizers

    def _register_randomizer_cls_wrapper(randomizer_cls: Any) -> Any:
        if not issubclass(randomizer_cls, (Randomizer,)):
            raise RegisterRandomizerError(
                f"Wrapped class must a Randomizer class. Got {randomizer_cls}"
            )
        site.register(randomizer_cls)
        return randomizer_cls

    return _register_randomizer_cls_wrapper
