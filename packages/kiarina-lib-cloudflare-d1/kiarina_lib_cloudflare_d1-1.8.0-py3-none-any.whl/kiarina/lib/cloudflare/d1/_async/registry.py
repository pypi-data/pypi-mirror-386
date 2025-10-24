from kiarina.lib.cloudflare.auth import settings_manager as auth_settings_manager

from ..settings import settings_manager
from .client import D1Client


def create_d1_client(
    config_key: str | None = None,
    *,
    auth_config_key: str | None = None,
) -> D1Client:
    """
    Create a D1 client.
    """
    settings = settings_manager.get_settings(config_key)
    auth_settings = auth_settings_manager.get_settings(auth_config_key)
    return D1Client(settings, auth_settings=auth_settings)
