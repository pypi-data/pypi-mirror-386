"""
TroveSuite Auth Package

A comprehensive authentication and authorization service for ERP systems.
Provides JWT token validation, user authorization, and permission checking.
"""

from .auth import AuthService

__version__ = "1.0.8"
__author__ = "Bright Debrah Owusu"
__email__ = "owusu.debrah@deladetech.com"

__all__ = [
    "AuthService"
]
