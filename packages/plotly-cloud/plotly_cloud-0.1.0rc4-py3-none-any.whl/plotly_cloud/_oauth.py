"""OAuth client implementation for Plotly Cloud CLI using WorkOS CLI Auth."""

import asyncio
import json
import os
import time
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import httpx
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from typing_extensions import TypedDict

from .exceptions import (
    CredentialError,
    OAuthClientError,
    TimeoutError,
    TokenError,
)

console = Console()

# WorkOS CLI Auth Configuration
WORKOS_API_BASE_URL = "https://api.workos.com"
WORKOS_ENDPOINTS = {
    "DEVICE_AUTHORIZE": "/user_management/authorize/device",
    "AUTHENTICATE": "/user_management/authenticate",
    "REFRESH_TOKEN": "/user_management/authenticate",
    "LOGOUT": "/user_management/sessions/logout",
}

# OAuth Configuration
DEFAULT_AUTH_PROVIDER = "authkit"


class AuthTokenResponse(TypedDict):
    """Response from successful OAuth authentication."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class AuthErrorResponse(TypedDict):
    """Response from failed OAuth authentication."""

    error: str
    error_description: Optional[str]


AuthResponse = Union[AuthTokenResponse, AuthErrorResponse]


class OAuthClient:
    """OAuth client for WorkOS CLI Auth using device authorization flow."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.credentials_path = self._get_credentials_path()

    def _get_credentials_path(self) -> Path:
        """Get cross-platform credentials file path."""
        home = Path.home()
        return home / ".plotly-cloud"

    async def request_device_authorization(self, provider: str = DEFAULT_AUTH_PROVIDER) -> dict:
        """Request device authorization from WorkOS CLI Auth."""
        if not self.client_id:
            raise OAuthClientError("client_id is required")

        device_auth_data = {
            "client_id": self.client_id,
            "provider": provider,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WORKOS_API_BASE_URL}{WORKOS_ENDPOINTS['DEVICE_AUTHORIZE']}",
                data=device_auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded", "user-agent": "PlotlyCloudCLI"},
            )

            if response.status_code != 200:
                raise OAuthClientError("Device authorization failed", response.text)

            return response.json()

    async def check_authentication_status(
        self,
        device_code: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Tuple[int, AuthResponse]:
        """Check authentication status without terminal output or polling loop.

        Args:
            device_code: The device code from device authorization
            client: Optional httpx client to use, creates new one if not provided

        Returns:
            Tuple of (status_code, response_data)
        """
        token_data = {
            "client_id": self.client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }

        if client:
            response = await client.post(
                f"{WORKOS_API_BASE_URL}{WORKOS_ENDPOINTS['AUTHENTICATE']}",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded", "user-agent": "PlotlyCloudCLI"},
            )
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.post(
                    f"{WORKOS_API_BASE_URL}{WORKOS_ENDPOINTS['AUTHENTICATE']}",
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded", "user-agent": "PlotlyCloudCLI"},
                )

        return response.status_code, response.json()

    async def poll_for_authentication(
        self, device_code: str, interval: int = 5, timeout: int = 300
    ) -> AuthTokenResponse:
        """Poll for authentication completion with exponential backoff."""
        start_time = time.time()
        current_interval = interval
        max_interval = 30  # Maximum polling interval

        spinner = Spinner("dots", text="⏳ Waiting for authorization...")

        with Live(spinner, console=console, refresh_per_second=4):
            async with httpx.AsyncClient() as client:
                while time.time() - start_time < timeout:
                    status_code, response_data = await self.check_authentication_status(device_code, client)

                    if status_code == 200:
                        return response_data  # type: ignore

                    error = response_data.get("error", "unknown_error")

                    if error == "authorization_pending":
                        # Continue polling
                        await asyncio.sleep(current_interval)
                        # Implement exponential backoff
                        current_interval = min(current_interval * 1.5, max_interval)
                        continue
                    elif error == "slow_down":
                        # Slow down polling
                        current_interval = min(current_interval * 2, max_interval)
                        spinner.text = f"🐌 Slowing down polling to {current_interval}s..."
                        await asyncio.sleep(current_interval)
                        spinner.text = "⏳ Waiting for authorization..."
                        continue
                    elif error == "expired_token":
                        raise TokenError("Device code expired. Please try again.")
                    elif error == "access_denied":
                        raise OAuthClientError("Access denied by user.")
                    else:
                        raise OAuthClientError("Authentication failed", error)

        raise TimeoutError("Authentication timed out. Please try again.")

    async def login(self, open_browser: bool = True, provider: str = DEFAULT_AUTH_PROVIDER) -> AuthTokenResponse:
        """Perform CLI Auth device flow login."""

        # Step 1: Request device authorization
        device_auth = await self.request_device_authorization(provider)

        device_code = device_auth["device_code"]
        user_code = device_auth["user_code"]
        verification_uri = device_auth["verification_uri"]
        verification_uri_complete = device_auth["verification_uri_complete"]
        expires_in = device_auth.get("expires_in", 300)
        interval = device_auth.get("interval", 5)

        # Step 2: Display user code and verification URI in a panel
        panel_content = (
            f"\n🌐 Verification URL: "
            f"[underline blue]{verification_uri}[/underline blue]\n"
            f"\n🔑 Device Code: [bold yellow]{user_code}[/bold yellow]\n"
        )

        if open_browser:
            panel_title = "🔐 Logging in to Plotly Cloud..."
            webbrowser.open(verification_uri_complete)
        else:
            panel_title = "📋 Please open the URL in your browser to authenticate"

        console.print()
        console.print(
            Panel(
                panel_content,
                title=panel_title,
                border_style="dim yellow",
                title_align="left",
            )
        )
        console.print()
        console.print()

        # Step 3: Poll for authentication completion
        try:
            tokens = await self.poll_for_authentication(device_code, interval, expires_in)
        except (OAuthClientError, TokenError, TimeoutError) as e:
            console.print(f"✗ Authentication failed: {e}")
            raise

        # Step 4: Save credentials
        await self._save_credentials(dict(tokens))

        return tokens

    async def _save_credentials(self, credentials: Dict[str, Any]):
        """Save credentials to file."""
        try:
            # Ensure parent directory exists
            self.credentials_path.parent.mkdir(exist_ok=True)

            # Write credentials
            with open(self.credentials_path, "w") as f:
                json.dump(credentials, f, indent=2)

            # Set secure permissions (readable only by owner)
            os.chmod(self.credentials_path, 0o600)

        except Exception as e:
            raise CredentialError("Failed to save credentials", str(e)) from e

    async def load_credentials(self) -> Optional[Dict[str, Any]]:
        """Load saved credentials."""
        try:
            if not self.credentials_path.exists():
                return None

            with open(self.credentials_path) as f:
                return json.load(f)

        except Exception as e:
            console.print(f"✗ Failed to load credentials: {e}")
            return None

    async def logout(self):
        """Logout and clear credentials."""
        credentials = await self.load_credentials()

        if credentials and "access_token" in credentials:
            # Call WorkOS logout endpoint
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{WORKOS_API_BASE_URL}{WORKOS_ENDPOINTS['LOGOUT']}",
                        headers={
                            "Authorization": f"Bearer {credentials['access_token']}",
                            "user-agent": "PlotlyCloudCLI",
                        },
                    )
            except Exception as e:
                console.print(f"⚠ Failed to logout from remote: {e}")
                # Continue with local cleanup even if remote logout fails

        # Clear local credentials
        if self.clear_credentials():
            console.print("Local credentials cleared")

    def clear_credentials(self):
        if self.credentials_path.exists():
            self.credentials_path.unlink()
            return True
        return False

    async def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        credentials = await self.load_credentials()
        return credentials is not None and "access_token" in credentials

    async def get_access_token(self) -> Optional[str]:
        """Get current access token."""
        credentials = await self.load_credentials()
        if credentials:
            return credentials.get("access_token")
        return None

    async def refresh_access_token(self) -> str:
        """Refresh the access token using the refresh token.

        Raises:
            TokenError: If no refresh token available or refresh fails
        """
        credentials = await self.load_credentials()
        if not credentials or "refresh_token" not in credentials:
            raise TokenError("No refresh token available")

        refresh_token = credentials["refresh_token"]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WORKOS_API_BASE_URL}{WORKOS_ENDPOINTS['REFRESH_TOKEN']}",
                data={
                    "client_id": self.client_id,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded", "user-agent": "PlotlyCloudCLI"},
            )

            if response.status_code == 200:
                new_tokens = response.json()
                # Update stored credentials with new tokens
                credentials.update(new_tokens)
                await self._save_credentials(credentials)
                return new_tokens["access_token"]
            else:
                raise TokenError("Token refresh failed", response.text)

    @property
    def access_token(self) -> Optional[str]:
        """Synchronous property to get access token for backward compatibility."""
        # This is a simplified sync version for compatibility
        # In practice, you should use get_access_token() async method
        try:
            if self.credentials_path.exists():
                with open(self.credentials_path) as f:
                    credentials = json.load(f)
                return credentials.get("access_token")
        except Exception:
            pass
        return None
