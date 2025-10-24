# __init__.py
import logging
from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._get_blob import get_blob
    from ._get_bucket import get_bucket
    from ._get_storage_client import get_storage_client
    from .settings import GoogleCloudStorageSettings, settings_manager

__version__ = version("kiarina-lib-google-cloud-storage")

__all__ = [
    # ._helpers
    "get_blob",
    "get_bucket",
    "get_storage_client",
    # .settings
    "GoogleCloudStorageSettings",
    "settings_manager",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    module_map = {
        # ._helpers
        "get_blob": "._get_blob",
        "get_bucket": "._get_bucket",
        "get_storage_client": "._get_storage_client",
        # .settings
        "GoogleCloudStorageSettings": ".settings",
        "settings_manager": ".settings",
    }

    globals()[name] = getattr(import_module(module_map[name], __name__), name)
    return globals()[name]
