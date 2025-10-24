from typing import Any

from google.cloud import storage  # type: ignore[import-untyped]
from kiarina.lib.google.auth import get_credentials


def get_storage_client(
    auth_config_key: str | None = None,
    **kwargs: Any,
) -> storage.Client:
    credentials = get_credentials(auth_config_key)
    return storage.Client(credentials=credentials, **kwargs)
