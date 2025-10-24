"""Configuration for GitHub OAuth (Device Flow).

This module provides configuration for GitHub's Device Flow OAuth, which is
designed for CLIs and doesn't require a client secret. The client_id is public
and safe to distribute in the codebase.

This configuration is part of the core library and can be used by CLI, Web API,
and Web UI interfaces.
"""

from dataclasses import dataclass


@dataclass
class GitHubOAuthConfig:
    """Configuration for GitHub OAuth (Device Flow).

    Device Flow is designed for CLIs and doesn't require a client secret.
    The client_id is public and safe to distribute in the codebase.
    """

    # Public GitHub app client ID - safe to distribute
    client_id: str = "Ov23liIBTV75Sjfu4Pay"
    scopes: str = "repo"

    # URLs for device flow
    device_code_url: str = "https://github.com/login/device/code"
    token_url: str = "https://github.com/login/oauth/access_token"
