import os
import tomllib
from typing import Dict, Any

# Default Configuration
DEFAULT_CONFIG = {
    "core": {
        "default_source": "arxiv",
        "search_limit": 10,
        "download_limit": None,
        "output_dir": "downloads",
        "convert_to_md": False,
    },
    "advanced": {
        "download_wait_min": 10.0,
        "download_wait_max": 40.0,
        "search_wait_min": 0.0,
        "search_wait_max": 2.0,
    },
    "api_keys": {
        "uspto": "",
    },
    "3gpp": {
        "convert_to_pdf": True,
    },
}


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.toml.
    Order of precedence:
    1. Local config (`./config.toml`)
    2. User config (`~/.config/paper-fetch/config.toml`)
    3. Default config
    """
    config = DEFAULT_CONFIG.copy()

    # Define paths to check
    paths = [
        os.path.expanduser("~/.config/paper-fetch/config.toml"),
        os.path.join(os.getcwd(), "config.toml"),
    ]

    # loaded_something = False

    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    user_config = tomllib.load(f)
                    _deep_merge(config, user_config)
                    # loaded_something = True
            except Exception as e:
                print(f"Warning: Failed to load config from {path}: {e}")

    return config


def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]):
    """Recursively merge update dict into base dict."""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
