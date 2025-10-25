from __future__ import annotations

from typing import NoReturn

from kelvin.api.base.http_client import env_vars
from kelvin.api.client import AsyncClient


class UnavailableApiClientError(Exception):
    """Raised when attempting to use an unavailable API client."""


class UnavailableApiClient(AsyncClient):
    def __init__(self, message: str):
        self.message = message

    def __getattr__(self, _: str) -> NoReturn:
        """Raises on attribute access."""
        raise UnavailableApiClientError(self.message)


def initialize_api_client() -> AsyncClient:
    """Validate required environment vars are available to create the API client
    Returns UnavailableApiClient mock client if requirements are not met.

    Returns:
        AsyncClient: The instantiated API client or an UnavailableApiClient if requirements are not met
    """
    client_vars = env_vars.EnvVars()

    if not client_vars.KELVIN_CLIENT.URL:
        return UnavailableApiClient("Kelvin API URL is not set.")

    if not (client_vars.KELVIN_CLIENT.CLIENT_ID and client_vars.KELVIN_CLIENT.CLIENT_SECRET) and not (
        client_vars.KELVIN_CLIENT.USERNAME and client_vars.KELVIN_CLIENT.PASSWORD
    ):
        return UnavailableApiClient("Kelvin API credentials are not set.")

    try:
        return AsyncClient()
    except Exception as e:
        return UnavailableApiClient(f"Failed to create Kelvin API client: {e}")
