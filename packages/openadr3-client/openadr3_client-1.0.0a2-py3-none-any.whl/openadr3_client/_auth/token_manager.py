from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from openadr3_client.logging import logger


@dataclass
class OAuthTokenManagerConfig:
    client_id: str
    client_secret: str
    token_url: str
    scopes: list[str] | None
    audience: str | None


class OAuthTokenManager:
    """An OAuth token manager responsible for the retrieval and caching of access tokens."""

    def __init__(self, config: OAuthTokenManagerConfig) -> None:
        self.client = BackendApplicationClient(
            client_id=config.client_id, scope=" ".join(config.scopes) if config.scopes is not None else None
        )
        self.oauth = OAuth2Session(client=self.client)
        self.token_url = config.token_url
        self.client_secret = config.client_secret
        self.audience = config.audience
        if self.token_url is None:
            msg = "token_url is required"
            raise ValueError(msg)

        if self.client_secret is None:
            msg = "client_secret is required"
            raise ValueError(msg)

        self._lock = Lock()
        self._cached_token: tuple[datetime, str] | None = None

    def get_access_token(self) -> str:
        """
        Retrieves an access token from the token manager.

        If a cached token is present in the token manager, this token is returned.
        If no cached token is present, a new token is fetched, cached and returned.

        Returns:
            str: The access token.

        """
        with self._lock:
            if self._cached_token:
                expiration_time, token = self._cached_token

                if expiration_time > datetime.now(tz=UTC):
                    return token

                # If we reach here, the token has reached its expiration time.
                # Remove the token and fetch a new one.
                self._cached_token = None

            return self._get_new_access_token()

    def _get_new_access_token(self) -> str:
        token_response = self.oauth.fetch_token(
            token_url=self.token_url, client_secret=self.client_secret, audience=self.audience
        )

        # Calculate expiration time (half of token lifetime)
        expires_in_seconds = token_response.get("expires_in", 3600)
        expiration_time = datetime.now(tz=UTC) + timedelta(seconds=expires_in_seconds // 2)

        access_token = token_response.get("access_token")

        if not access_token:
            logger.error("OAuthTokenManager - access_token not present in response")
            exc_msg = "Access token was not present in token response"
            raise ValueError(exc_msg)

        self._cached_token = (expiration_time, access_token)
        return access_token
