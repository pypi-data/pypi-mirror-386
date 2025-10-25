"""Testing utilities for django-bolt.

Provides test clients for in-memory testing without subprocess/network overhead.
"""
from django_bolt.testing.client import TestClient

__all__ = [
    "TestClient",
]
