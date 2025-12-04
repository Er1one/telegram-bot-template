"""Pytest configuration and fixtures."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest


@pytest.fixture
def event_loop_policy():
    """Set the event loop policy for pytest-asyncio."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
