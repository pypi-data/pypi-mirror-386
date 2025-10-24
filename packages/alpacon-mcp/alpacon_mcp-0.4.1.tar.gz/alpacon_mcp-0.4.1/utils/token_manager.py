"""Token management utilities for Alpacon MCP server."""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
from utils.logger import get_logger

logger = get_logger("token_manager")


class TokenManager:
    """Manages API tokens for different regions and workspaces."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize token manager.

        Args:
            config_file: Full path to config file. If None, uses ALPACON_CONFIG_FILE env var
                        or defaults to global config (~/.alpacon-mcp/token.json)
        """
        if config_file:
            # Use specific config file path, expand ~ to home directory
            expanded_path = os.path.expanduser(config_file)
            self.token_file = Path(expanded_path)
            logger.info(f"Using specified config file: {self.token_file}")
        else:
            # Check environment variable first
            env_config_file = os.getenv("ALPACON_MCP_CONFIG_FILE")
            if env_config_file:
                # Expand ~ to home directory
                expanded_path = os.path.expanduser(env_config_file)
                self.token_file = Path(expanded_path)
                logger.info(f"Using config file from environment: {self.token_file}")
            else:
                # Use global config by default, fall back to local
                global_config = Path.home() / ".alpacon-mcp" / "token.json"
                local_config = Path("config/token.json")

                if global_config.exists():
                    self.token_file = global_config
                    logger.info(f"Using global config file: {self.token_file}")
                elif local_config.exists():
                    self.token_file = local_config
                    logger.info(f"Using local config file: {self.token_file}")
                else:
                    # Default to global config location
                    self.token_file = global_config
                    logger.info(f"No config found, will use global location: {self.token_file}")

        self.config_dir = self.token_file.parent

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Config directory created/verified: {self.config_dir}")

        self.tokens = self._load_tokens()

    def _load_tokens(self) -> Dict[str, Any]:
        """Load tokens from configuration file.

        Returns:
            Dictionary containing token data
        """
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
                logger.info(f"Loaded tokens from {self.token_file}: {len(tokens)} regions")
                return tokens
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in {self.token_file}: {e}")
            except IOError as e:
                logger.error(f"IO error reading {self.token_file}: {e}")

        logger.warning(f"No valid token file found at {self.token_file}, starting with empty tokens")
        return {}

    def _save_tokens_to_file(self, tokens: Dict[str, Any], file_path: Path) -> None:
        """Save tokens to specific file.

        Args:
            tokens: Token data to save
            file_path: Path to save the tokens
        """
        # Ensure directory exists
        file_path.parent.mkdir(exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(tokens, f, indent=2)

    def _save_tokens(self) -> None:
        """Save tokens to configuration file."""
        self._save_tokens_to_file(self.tokens, self.token_file)

    def set_token(self, region: str, workspace: str, token: str) -> Dict[str, str]:
        """Set token for specific region and workspace.

        Args:
            region: Region (ap1, us1, eu1, etc.)
            workspace: Workspace name
            token: API token

        Returns:
            Success message with details
        """
        if region not in self.tokens:
            self.tokens[region] = {}

        # Simplified structure: region -> workspace -> token (string only)
        self.tokens[region][workspace] = token

        self._save_tokens()

        return {
            "status": "success",
            "message": f"Token saved for {workspace}.{region}",
            "region": region,
            "workspace": workspace
        }

    def get_token(self, region: str, workspace: str) -> Optional[str]:
        """Get token for specific region and workspace.

        Args:
            region: Region (ap1, us1, eu1, etc.)
            workspace: Workspace name

        Returns:
            Token string if found, None otherwise
        """
        logger.debug(f"Getting token for {workspace}.{region}")

        # First try environment variable: ALPACON_MCP_<REGION>_<WORKSPACE>_TOKEN
        env_var_name = f"ALPACON_MCP_{region.upper()}_{workspace.upper()}_TOKEN"
        env_token = os.getenv(env_var_name)
        if env_token:
            logger.info(f"Found token for {workspace}.{region} from environment variable")
            return env_token

        # Fall back to config file
        if region in self.tokens and workspace in self.tokens[region]:
            logger.info(f"Found token for {workspace}.{region} from config file")
            return self.tokens[region][workspace]

        logger.warning(f"No token found for {workspace}.{region}")
        return None

    def get_all_tokens(self) -> Dict[str, Any]:
        """Get all stored tokens.

        Returns:
            All token data
        """
        return self.tokens

    def remove_token(self, region: str, workspace: str) -> Dict[str, str]:
        """Remove token for specific region and workspace.

        Args:
            region: Region (ap1, us1, eu1, etc.)
            workspace: Workspace name

        Returns:
            Success or error message
        """
        if region in self.tokens and workspace in self.tokens[region]:
            del self.tokens[region][workspace]

            # Clean up empty region
            if not self.tokens[region]:
                del self.tokens[region]

            self._save_tokens()

            return {
                "status": "success",
                "message": f"Token removed for {workspace}.{region}"
            }

        return {
            "status": "error",
            "message": f"No token found for {workspace}.{region}"
        }

    def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication status for all stored tokens.

        Returns:
            Authentication status information
        """
        total_tokens = sum(len(workspaces) for workspaces in self.tokens.values())

        regions = []
        for region, workspaces in self.tokens.items():
            regions.append({
                "region": region,
                "workspaces": list(workspaces.keys()),
                "count": len(workspaces)
            })

        return {
            "authenticated": total_tokens > 0,
            "total_tokens": total_tokens,
            "regions": regions,
            "config_dir": str(self.config_dir),
            "token_file": str(self.token_file)
        }

    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration directory information.

        Returns:
            Configuration directory details
        """
        return {
            "config_dir": str(self.config_dir),
            "token_file": str(self.token_file),
            "token_file_exists": self.token_file.exists(),
            "env_config_file": os.getenv("ALPACON_CONFIG_FILE")
        }


# Global token manager instance
_global_token_manager = None

def get_token_manager() -> TokenManager:
    """Get the global token manager instance.

    Returns:
        Global TokenManager instance
    """
    global _global_token_manager
    if _global_token_manager is None:
        # Let TokenManager handle config file resolution logic
        _global_token_manager = TokenManager()
    return _global_token_manager