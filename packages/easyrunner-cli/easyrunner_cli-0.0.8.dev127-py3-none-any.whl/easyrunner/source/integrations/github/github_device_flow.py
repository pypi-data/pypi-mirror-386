"""GitHub Device Flow authentication.

This module implements GitHub's Device Flow OAuth, which is designed for
CLIs and other applications that don't require a client secret. Users authorize
the app by visiting a URL and entering a code.

This is part of the core library and can be used by CLI, Web API, and Web UI.
HttpClient is injected for HTTP operations, making it easy to test and swap
implementations.
"""

import logging
import time
import webbrowser
from dataclasses import dataclass
from typing import Callable, Optional

from ...http_client import HttpClient

logger = logging.getLogger(__name__)


@dataclass
class DeviceCodeResponse:
    """Response from device code request."""

    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


class GitHubDeviceFlow:
    """GitHub Device Flow authentication.

    This class uses HttpClient for all HTTP operations, making it easy to:
    - Test with mock HTTP client
    - Use different HTTP implementations (sync/async)
    - Consistent error handling across all interfaces
    """

    DEVICE_CODE_URL = "https://github.com/login/device/code"
    TOKEN_URL = "https://github.com/login/oauth/access_token"

    def __init__(
        self,
        client_id: str,
        scopes: str = "repo",
        progress_callback: Optional[Callable[[str, str], None]] = None,
        http_client: Optional[HttpClient] = None,
    ):
        """Initialize device flow.

        Args:
            client_id: GitHub OAuth app client ID (public, safe to distribute)
            scopes: OAuth scopes to request (default: "repo")
            progress_callback: Optional callback for progress messages
            http_client: Optional HttpClient instance. Defaults to new HttpClient().
        """
        self.client_id = client_id
        self.scopes = scopes
        self.http_client = http_client or HttpClient()
        self.progress_callback = progress_callback or (lambda msg, end: None)

    def start_device_flow(self) -> Optional[str]:
        """Start device flow and return access token if successful."""
        try:
            # Step 1: Request device code
            device_response = self._request_device_code()
            if not device_response:
                self.progress_callback(
                    "[red]❌ Failed to request device code[/red]", "\n"
                )
                return None

            # Step 2: Show user instructions
            self._display_user_instructions(device_response)

            # Step 3: Poll for token
            return self._poll_for_token(device_response)

        except Exception as e:
            logger.error(f"Device flow failed: {e}")
            self.progress_callback(f"[red]❌ Device flow failed: {e}[/red]", "\n")
            return None

    def _request_device_code(self) -> Optional[DeviceCodeResponse]:
        """Request device code from GitHub."""
        try:
            request_data = {"client_id": self.client_id, "scope": self.scopes}

            response = self.http_client.post(
                self.DEVICE_CODE_URL,
                json_data=request_data,
                headers={"Accept": "application/json"},
            )

            if response.success and isinstance(response.data, dict):
                response_data = response.data

                # Check for GitHub API errors
                if "error" in response_data:
                    error = response_data.get("error")
                    error_desc = response_data.get("error_description", "Unknown error")
                    logger.error(f"GitHub API error: {error} - {error_desc}")
                    self.progress_callback(
                        f"[red]❌ GitHub Error: {error_desc}[/red]", "\n"
                    )
                    if error == "device_flow_disabled":
                        self.progress_callback(
                            "[yellow]💡 Device Flow must be enabled in GitHub OAuth app settings[/yellow]",
                            "\n",
                        )
                        self.progress_callback(
                            "[yellow]   Visit: https://github.com/settings/developers[/yellow]",
                            "\n",
                        )
                    return None

                return DeviceCodeResponse(
                    device_code=response_data["device_code"],
                    user_code=response_data["user_code"],
                    verification_uri=response_data["verification_uri"],
                    expires_in=response_data["expires_in"],
                    interval=response_data["interval"],
                )

            logger.error(f"Device code request failed: {response.error}")
            return None

        except Exception as e:
            logger.error(f"Failed to request device code: {e}")
            return None

    def _display_user_instructions(self, device_response: DeviceCodeResponse) -> None:
        """Display instructions to user."""
        self.progress_callback("\n" + "=" * 60, "\n")
        self.progress_callback("🔐 [bold cyan]GitHub Device Authorization[/bold cyan]", "\n")
        self.progress_callback("=" * 60, "\n\n")
        self.progress_callback(
            f"1. Visit: [bold blue]{device_response.verification_uri}[/bold blue]",
            "\n",
        )
        self.progress_callback(
            f"2. Enter code: [bold yellow]{device_response.user_code}[/bold yellow]",
            "\n\n",
        )
        self.progress_callback("🌐 Opening browser...", "\n")

        # Auto-open browser
        try:
            webbrowser.open(device_response.verification_uri)
        except Exception as e:
            logger.warning(f"Failed to open browser: {e}")

        self.progress_callback("\n⏳ Waiting for authorization", "")

    def _poll_for_token(self, device_response: DeviceCodeResponse) -> Optional[str]:
        """Poll GitHub for access token."""
        interval = device_response.interval
        expires_at = time.time() + device_response.expires_in
        poll_count = 0

        while time.time() < expires_at:
            time.sleep(interval)

            # Show progress dots
            poll_count += 1
            if poll_count % 3 == 0:
                self.progress_callback(".", "")

            token_data = {
                "client_id": self.client_id,
                "device_code": device_response.device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            }

            response = self.http_client.post(
                self.TOKEN_URL,
                json_data=token_data,
                headers={"Accept": "application/json"},
            )

            if response.success and isinstance(response.data, dict):
                response_data = response.data

                # Success - token received
                if "access_token" in response_data:
                    self.progress_callback("\n", "\n")
                    return response_data["access_token"]

                # Handle errors
                error = response_data.get("error")

                if error == "authorization_pending":
                    # Keep polling
                    continue
                elif error == "slow_down":
                    # Increase interval as requested by GitHub
                    interval += 5
                    continue
                elif error == "expired_token":
                    self.progress_callback(
                        "\n[red]❌ Device code expired. Please try again.[/red]", "\n"
                    )
                    return None
                elif error == "access_denied":
                    self.progress_callback(
                        "\n[red]❌ Authorization denied by user.[/red]", "\n"
                    )
                    return None
                else:
                    logger.error(f"Unknown error during polling: {error}")
                    self.progress_callback(
                        f"\n[red]❌ Authorization failed: {error}[/red]", "\n"
                    )
                    return None

        self.progress_callback("\n[red]❌ Authorization timed out.[/red]", "\n")
        return None

    def test_token(self, token: str) -> bool:
        """Test if token is valid by making a test API call."""
        try:
            response = self.http_client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {token}"},
            )

            return (
                response.success
                and response.data is not None
                and isinstance(response.data, dict)
                and "login" in response.data
            )

        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False
