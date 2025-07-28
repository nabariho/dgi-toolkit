#!/usr/bin/env python3
"""
Demonstration of the enhanced configuration management system.

This script shows how to use the new configuration management features:
- Multiple configuration sources with priority ordering
- Environment variable configuration
- File-based configuration (JSON, YAML)
- Default configuration values
- Configuration validation and hot-reload
"""

import json
import os
import tempfile
from pathlib import Path

from dgi.config import CoreSettings
from dgi.config_management import (
    ConfigurationManager,
)


def demo_basic_configuration():
    """Demonstrate basic configuration loading."""
    print("=== Basic Configuration Demo ===")

    # Create a configuration manager for core settings
    manager = ConfigurationManager(CoreSettings)

    # Add default configuration
    manager.add_default_config(
        {
            "log_level": "DEBUG",
            "default_min_yield": 3.0,
            "default_max_payout": 70.0,
            "default_min_cagr": 8.0,
        }
    )

    # Load settings
    settings = manager.load_settings()
    print(f"Log level: {settings.log_level}")
    print(f"Min yield: {settings.default_min_yield}")
    print(f"Max payout: {settings.default_max_payout}")
    print(f"Min CAGR: {settings.default_min_cagr}")
    print()


def demo_environment_config():
    """Demonstrate environment variable configuration."""
    print("=== Environment Configuration Demo ===")

    # Set some environment variables
    os.environ["DGI_CORE_log_level"] = "WARNING"
    os.environ["DGI_CORE_default_min_yield"] = "4.0"

    manager = ConfigurationManager(CoreSettings)
    manager.add_environment_config("DGI_CORE_")
    manager.add_default_config(
        {
            "log_level": "INFO",
            "default_min_yield": 2.0,
            "default_max_payout": 80.0,
            "default_min_cagr": 5.0,
        }
    )

    settings = manager.load_settings()
    print(f"Log level (from env): {settings.log_level}")
    print(f"Min yield (from env): {settings.default_min_yield}")
    print(f"Max payout (from default): {settings.default_max_payout}")
    print()

    # Clean up
    del os.environ["DGI_CORE_log_level"]
    del os.environ["DGI_CORE_default_min_yield"]


def demo_file_config():
    """Demonstrate file-based configuration."""
    print("=== File Configuration Demo ===")

    # Create temporary config files
    with tempfile.TemporaryDirectory() as temp_dir:
        # JSON config file
        json_config = {
            "log_level": "ERROR",
            "default_min_yield": 5.0,
            "default_max_payout": 60.0,
        }
        json_file = Path(temp_dir) / "config.json"
        with open(json_file, "w") as f:
            json.dump(json_config, f)

        # YAML config file (higher priority due to alphabetical loading)
        yaml_config = """
log_level: CRITICAL
default_min_cagr: 12.0
"""
        yaml_file = Path(temp_dir) / "override.yaml"
        with open(yaml_file, "w") as f:
            f.write(yaml_config)

        manager = ConfigurationManager(CoreSettings)
        manager.add_file_config(json_file, watch=False)  # Disable watching for demo
        manager.add_file_config(yaml_file, watch=False)
        manager.add_default_config(
            {
                "log_level": "INFO",
                "default_min_yield": 2.0,
                "default_max_payout": 80.0,
                "default_min_cagr": 5.0,
            }
        )

        settings = manager.load_settings()
        print(f"Log level (from YAML): {settings.log_level}")
        print(f"Min yield (from JSON): {settings.default_min_yield}")
        print(f"Max payout (from JSON): {settings.default_max_payout}")
        print(f"Min CAGR (from YAML): {settings.default_min_cagr}")
        print()


def demo_priority_ordering():
    """Demonstrate configuration priority ordering."""
    print("=== Configuration Priority Demo ===")

    # Set environment variable
    os.environ["DGI_DEMO_log_level"] = "CRITICAL"

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config file
        config_file = Path(temp_dir) / "demo.json"
        with open(config_file, "w") as f:
            json.dump({"log_level": "WARNING", "default_min_yield": 6.0}, f)

        manager = ConfigurationManager(CoreSettings)

        # Add sources in reverse priority order to show ordering works
        manager.add_default_config({"log_level": "DEBUG", "default_min_yield": 1.0})
        manager.add_file_config(config_file, watch=False)
        manager.add_environment_config("DGI_DEMO_")

        settings = manager.load_settings()
        print("Priority order: Environment > File > Default")
        print(f"Log level: {settings.log_level} (should be CRITICAL from env)")
        print(f"Min yield: {settings.default_min_yield} (should be 6.0 from file)")
        print()

    # Clean up
    del os.environ["DGI_DEMO_log_level"]


def demo_validation_errors():
    """Demonstrate configuration validation."""
    print("=== Configuration Validation Demo ===")

    manager = ConfigurationManager(CoreSettings)

    # Add invalid configuration
    manager.add_default_config(
        {
            "log_level": "INVALID_LEVEL",  # This will cause validation error
            "default_min_yield": "not_a_number",  # This will also fail
        }
    )

    try:
        manager.load_settings()
        print("This shouldn't print if validation works")
    except Exception as e:
        print(f"Validation error (expected): {type(e).__name__}")
        print(f"Error message: {str(e)[:100]}...")
        print()


def demo_temporary_config():
    """Demonstrate temporary configuration overrides."""
    print("=== Temporary Configuration Demo ===")

    manager = ConfigurationManager(CoreSettings)
    manager.add_default_config(
        {
            "log_level": "INFO",
            "default_min_yield": 2.0,
        }
    )

    # Load initial settings
    settings = manager.load_settings()
    print(f"Original log level: {settings.log_level}")
    print(f"Original min yield: {settings.default_min_yield}")

    # Use temporary override
    with manager.temporary_config({"log_level": "DEBUG", "default_min_yield": 10.0}):
        temp_settings = manager.get_current_settings()
        print(f"Temporary log level: {temp_settings.log_level}")
        print(f"Temporary min yield: {temp_settings.default_min_yield}")

    # Check that settings are restored
    restored_settings = manager.get_current_settings()
    print(f"Restored log level: {restored_settings.log_level}")
    print(f"Restored min yield: {restored_settings.default_min_yield}")
    print()


def main():
    """Run all configuration demos."""
    print("🔧 Enhanced Configuration Management System Demo\n")

    demo_basic_configuration()
    demo_environment_config()
    demo_file_config()
    demo_priority_ordering()
    demo_validation_errors()
    demo_temporary_config()

    print("✅ Configuration management demo completed!")
    print("\nKey features demonstrated:")
    print("- Multiple configuration sources (env, file, default)")
    print("- Priority-based configuration composition")
    print("- Automatic validation with Pydantic")
    print("- Temporary configuration overrides")
    print("- Error handling for invalid configurations")


if __name__ == "__main__":
    main()
