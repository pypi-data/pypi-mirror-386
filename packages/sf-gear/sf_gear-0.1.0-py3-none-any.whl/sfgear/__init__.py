"""
SF Gear (sfgear) - A Python library for Salesforce API and CLI integration.

This library provides modules for Salesforce operations:
- cli: Wrapper around Salesforce CLI commands
- api: Wrapper around Salesforce REST APIs (coming in future versions)
"""

from . import cli

__version__ = "0.1.0"
__author__ = "Alexander Hooke"
__email__ = "alexander.hooke@gmail.com"

__all__ = [
    "cli",
]
