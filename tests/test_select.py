import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from awenta_ahr.select import AwentaModeSelect, async_setup_entry, MODE_MAP
from awenta_ahr.const import DOMAIN


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {"AA:BB:CC:DD:EE:FF": {"mode": 2, "power": True}}
    return coordinator


@pytest.fixture
def mock_api():
    """Create a mock API."""
    api = MagicMock()
    api.send = AsyncMock()
    api.last_modes = {}
    api.devices = [{"mac": "AA:BB:CC:DD:EE:FF", "name": "Test Device"}]
    return api


@pytest.fixture
def mock_hass(mock_coordinator, mock_api):
    hass = MagicMock()
    hass.data = {DOMAIN: {"test_entry_id": {"api": mock_api, "coordinator": mock_coordinator}}}
    return hass


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    return entry


def test_select_options_list(mock_coordinator, mock_api):
    """Test that select entity has the correct options."""
    select = AwentaModeSelect(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")
    assert select._attr_options == list(MODE_MAP.keys())


def test_current_option_power_on(mock_coordinator, mock_api):
    """Test that current option returns the actual mode when power is on."""
    select = AwentaModeSelect(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")
    assert select.current_option == "Recuperation"


def test_current_option_power_off_with_last_mode(mock_coordinator, mock_api):
    """Test that current option returns last mode when power is off and last mode is available."""
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["power"] = False
    mock_api.last_modes["AA:BB:CC:DD:EE:FF"] = 1  # Supply
    select = AwentaModeSelect(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")
    assert select.current_option == "Supply"


def test_current_option_power_off_no_last_mode(mock_coordinator, mock_api):
    """Test that current option returns current mode when power is off and last mode is unavailable."""
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["power"] = False
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["mode"] = 0  # Extract
    select = AwentaModeSelect(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")
    assert select.current_option == "Extract"


@pytest.mark.asyncio
async def test_async_select_option(mock_coordinator, mock_api):
    """Test that selecting an option calls the API correctly and updates last_modes."""
    select = AwentaModeSelect(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")
    select.async_write_ha_state = MagicMock()

    await select.async_select_option("Supply")

    mock_api.send.assert_called_once_with(
        "AA:BB:CC:DD:EE:FF",
        {
            "act": "send_work_mode",
            "mode_nr": 1,
        },
    )
    assert mock_api.last_modes["AA:BB:CC:DD:EE:FF"] == 1
    select.async_write_ha_state.assert_called_once()


@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass, mock_entry):
    """Test async_setup_entry creates the entities."""
    async_add_entities = MagicMock()

    await async_setup_entry(mock_hass, mock_entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], AwentaModeSelect)
    assert entities[0]._attr_name == "Test Device Mode"