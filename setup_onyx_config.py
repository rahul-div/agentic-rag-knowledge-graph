#!/usr/bin/env python3
"""
Onyx Cloud Configuration Setup Script

This script helps you set up your Onyx Cloud Enterprise API configuration
by guiding you through the process and updating your .env file.

Usage:
    python setup_onyx_config.py
"""

import os
import re
from pathlib import Path


def get_current_env_values():
    """Get current environment values from .env file if it exists."""
    env_file = Path(".env")
    current_values = {}
    
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            current_values[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️  Warning: Could not read .env file: {e}")
    
    return current_values


def validate_api_key(api_key):
    """Basic validation for API key format."""
    if not api_key:
        return False, "API key cannot be empty"
    
    if len(api_key) < 10:
        return False, "API key seems too short"
    
    # Basic format check (this may vary by Onyx version)
    if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
        return False, "API key contains invalid characters"
    
    return True, "API key format looks valid"


def validate_base_url(base_url):
    """Validate base URL format."""
    if not base_url:
        return False, "Base URL cannot be empty"
    
    if not base_url.startswith(('http://', 'https://')):
        return False, "Base URL must start with http:// or https://"
    
    if base_url.endswith('/'):
        return False, "Base URL should not end with a slash"
    
    # Check for common Onyx Cloud patterns
    if 'onyx' not in base_url.lower():
        print("⚠️  Warning: URL doesn't contain 'onyx' - please verify this is correct")
    
    return True, "Base URL format looks valid"


def update_env_file(config_values):
    """Update the .env file with new configuration values."""
    env_file = Path(".env")
    
    # Read existing .env content
    existing_lines = []
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                existing_lines = f.readlines()
        except Exception as e:
            print(f"⚠️  Warning: Could not read existing .env file: {e}")
    
    # Track which Onyx keys we've updated
    updated_keys = set()
    new_lines = []
    
    # Process existing lines
    for line in existing_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key.startswith('ONYX_'):
                if key in config_values:
                    # Update with new value
                    new_lines.append(f"{key}={config_values[key]}\n")
                    updated_keys.add(key)
                else:
                    # Keep existing value
                    new_lines.append(line)
            else:
                # Keep non-Onyx line as-is
                new_lines.append(line)
        else:
            # Keep comments and empty lines
            new_lines.append(line)
    
    # Add any new Onyx keys that weren't in the file
    onyx_keys_to_add = set(config_values.keys()) - updated_keys
    if onyx_keys_to_add:
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines.append('\n')
        new_lines.append('\n# Onyx Cloud Enterprise Configuration\n')
        for key in sorted(onyx_keys_to_add):
            new_lines.append(f"{key}={config_values[key]}\n")
    
    # Write updated .env file
    try:
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"❌ Error writing .env file: {e}")
        return False


def main():
    """Main setup function."""
    print("🔧 ONYX CLOUD ENTERPRISE CONFIGURATION SETUP")
    print("=" * 50)
    print()
    
    print("This script will help you configure your Onyx Cloud Enterprise API settings.")
    print("You'll need your API key and base URL from your Onyx Cloud dashboard.")
    print()
    
    # Get current values
    current_values = get_current_env_values()
    
    # Collect configuration
    config_values = {}
    
    # API Key
    print("1. API KEY CONFIGURATION")
    print("-" * 25)
    current_api_key = current_values.get('ONYX_API_KEY', '')
    if current_api_key:
        print(f"Current API key: {current_api_key[:10]}...{current_api_key[-4:]}")
        use_current = input("Use current API key? (y/n): ").lower().strip()
        if use_current == 'y':
            config_values['ONYX_API_KEY'] = current_api_key
        else:
            api_key = input("Enter your Onyx Cloud API key: ").strip()
            is_valid, message = validate_api_key(api_key)
            print(f"   {message}")
            if is_valid:
                config_values['ONYX_API_KEY'] = api_key
            else:
                print("❌ Invalid API key. Please check and try again.")
                return
    else:
        api_key = input("Enter your Onyx Cloud API key: ").strip()
        is_valid, message = validate_api_key(api_key)
        print(f"   {message}")
        if is_valid:
            config_values['ONYX_API_KEY'] = api_key
        else:
            print("❌ Invalid API key. Please check and try again.")
            return
    
    print()
    
    # Base URL
    print("2. BASE URL CONFIGURATION")
    print("-" * 26)
    current_base_url = current_values.get('ONYX_BASE_URL', '')
    if current_base_url:
        print(f"Current base URL: {current_base_url}")
        use_current = input("Use current base URL? (y/n): ").lower().strip()
        if use_current == 'y':
            config_values['ONYX_BASE_URL'] = current_base_url
        else:
            base_url = input("Enter your Onyx Cloud base URL (e.g., https://your-company.onyx.app): ").strip()
            is_valid, message = validate_base_url(base_url)
            print(f"   {message}")
            if is_valid:
                config_values['ONYX_BASE_URL'] = base_url
            else:
                print("❌ Invalid base URL. Please check and try again.")
                return
    else:
        print("Example: https://your-company.onyx.app")
        base_url = input("Enter your Onyx Cloud base URL: ").strip()
        is_valid, message = validate_base_url(base_url)
        print(f"   {message}")
        if is_valid:
            config_values['ONYX_BASE_URL'] = base_url
        else:
            print("❌ Invalid base URL. Please check and try again.")
            return
    
    print()
    
    # Timeout (optional)
    print("3. TIMEOUT CONFIGURATION (optional)")
    print("-" * 35)
    current_timeout = current_values.get('ONYX_TIMEOUT', '30')
    print(f"Current timeout: {current_timeout} seconds")
    timeout_input = input(f"Enter timeout in seconds (press Enter for {current_timeout}): ").strip()
    
    if timeout_input:
        try:
            timeout_value = int(timeout_input)
            if timeout_value > 0:
                config_values['ONYX_TIMEOUT'] = str(timeout_value)
            else:
                print("⚠️  Using default timeout of 30 seconds")
                config_values['ONYX_TIMEOUT'] = '30'
        except ValueError:
            print("⚠️  Invalid timeout value. Using default of 30 seconds")
            config_values['ONYX_TIMEOUT'] = '30'
    else:
        config_values['ONYX_TIMEOUT'] = current_timeout
    
    print()
    
    # Confirm configuration
    print("4. CONFIGURATION SUMMARY")
    print("-" * 24)
    print(f"API Key: {config_values['ONYX_API_KEY'][:10]}...{config_values['ONYX_API_KEY'][-4:]}")
    print(f"Base URL: {config_values['ONYX_BASE_URL']}")
    print(f"Timeout: {config_values['ONYX_TIMEOUT']} seconds")
    print()
    
    confirm = input("Save this configuration to .env file? (y/n): ").lower().strip()
    if confirm != 'y':
        print("❌ Configuration cancelled.")
        return
    
    # Update .env file
    if update_env_file(config_values):
        print("✅ Configuration saved successfully!")
        print()
        print("NEXT STEPS:")
        print("-" * 10)
        print("1. Run the diagnostic tool to test connectivity:")
        print("   python diagnose_onyx_api.py")
        print()
        print("2. If diagnostic passes, run the integration test:")
        print("   python test_onyx_integration.py")
        print()
        print("3. Check your Onyx Cloud UI for the test document")
    else:
        print("❌ Failed to save configuration to .env file")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
