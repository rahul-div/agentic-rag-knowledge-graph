"""
Configuration management for Onyx API settings and environment variables.

This module handles loading and validation of Onyx-related configuration
from environment variables with sensible defaults for optional settings.
"""

import os
from typing import Dict


def get_onyx_config() -> Dict[str, str]:
    """
    Load Onyx configuration from environment variables.
    
    Returns:
        Dict[str, str]: Configuration dictionary with api_key, base_url, and timeout settings
        
    Raises:
        ValueError: If required ONYX_API_KEY is not set
        
    Environment Variables:
        ONYX_API_KEY (required): API key for Onyx authentication
        ONYX_BASE_URL (optional): Base URL for Onyx API (defaults to http://localhost:3000)
        ONYX_TIMEOUT (optional): Request timeout in seconds (defaults to 30)
    """
    api_key = os.getenv("ONYX_API_KEY")
    if not api_key:
        raise ValueError(
            "ONYX_API_KEY environment variable is required. "
            "Please set it to your Onyx API key."
        )
    
    base_url = os.getenv("ONYX_BASE_URL", "http://localhost:3000")
    timeout = os.getenv("ONYX_TIMEOUT", "30")
    
    # Validate timeout is a valid integer
    try:
        timeout_int = int(timeout)
        if timeout_int <= 0:
            raise ValueError("ONYX_TIMEOUT must be a positive integer")
    except ValueError as e:
        raise ValueError(f"Invalid ONYX_TIMEOUT value '{timeout}': {e}")
    
    # Validate base URL format
    if not base_url.startswith(("http://", "https://")):
        raise ValueError(
            f"Invalid ONYX_BASE_URL '{base_url}': must start with http:// or https://"
        )
    
    return {
        "api_key": api_key,
        "base_url": base_url.rstrip("/"),  # Remove trailing slash
        "timeout": timeout
    }


def validate_config(config: Dict[str, str]) -> bool:
    """
    Validate that a configuration dictionary contains required fields.
    
    Args:
        config (Dict[str, str]): Configuration dictionary to validate
        
    Returns:
        bool: True if configuration is valid
        
    Raises:
        ValueError: If configuration is missing required fields or has invalid values
    """
    required_fields = ["api_key", "base_url", "timeout"]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Configuration missing required field: {field}")
        
        if not config[field]:
            raise ValueError(f"Configuration field '{field}' cannot be empty")
    
    # Additional validation
    if not config["base_url"].startswith(("http://", "https://")):
        raise ValueError(f"Invalid base_url: {config['base_url']}")
    
    try:
        timeout_int = int(config["timeout"])
        if timeout_int <= 0:
            raise ValueError("timeout must be a positive integer")
    except ValueError:
        raise ValueError(f"Invalid timeout value: {config['timeout']}")
    
    return True
