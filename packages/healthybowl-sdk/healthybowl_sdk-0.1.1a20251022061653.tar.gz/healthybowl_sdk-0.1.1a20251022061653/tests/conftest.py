"""Pytest configuration and fixtures.

Ensures the package can be imported without installation
by adjusting sys.path.
"""

import sys
import warnings
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from boiler_sdk import BoilerSDK, BoilerSDKConfig  # noqa: E402

# Suppress specific async mock warnings
warnings.filterwarnings(
    "ignore",
    message="coroutine 'AsyncMockMixin._execute_mock_call' was never awaited",
)
warnings.filterwarnings("ignore", category=RuntimeWarning, module=".*")


@pytest.fixture
def sdk_config():
    """Basic SDK configuration for testing"""
    return BoilerSDKConfig(
        endpoint="https://api.test.com/graphql",
        api_key="test-api-key",
    )


@pytest.fixture
def sdk(sdk_config):
    """SDK instance for testing"""
    return BoilerSDK(sdk_config)


@pytest.fixture
async def async_sdk(sdk_config):
    """Async SDK instance with proper cleanup"""
    sdk = BoilerSDK(sdk_config)
    yield sdk
    await sdk.client.close()
