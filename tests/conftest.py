import pytest
from unittest.mock import patch
import sys
from pathlib import Path

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield

@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with patch(
        "custom_components.awenta_ahr.async_setup_entry",
        return_value=True,
    ):
        yield
