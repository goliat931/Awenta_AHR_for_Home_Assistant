import pytest
from unittest.mock import patch
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.awenta_ahr.const import DOMAIN


@pytest.mark.asyncio
async def test_show_form(hass: HomeAssistant) -> None:
    """Test that the setup form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_create_entry(hass: HomeAssistant) -> None:
    """Test we can create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={
            "email": "test@example.com",
            "password": "test-password",
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Awenta HRV"
    assert result["data"] == {
        "email": "test@example.com",
        "password": "test-password",
    }
    assert result["result"].unique_id == "test@example.com"


@pytest.mark.asyncio
async def test_duplicate_entry(hass: HomeAssistant) -> None:
    """Test that configuring an existing unique ID aborts."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test@example.com",
        data={
            "email": "test@example.com",
            "password": "old-password",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={
            "email": "test@example.com",
            "password": "test-password",
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
