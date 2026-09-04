import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from homeassistant.components.fan import FanEntityFeature
from awenta_ahr.fan import AwentaFan


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {"AA:BB:CC:DD:EE:FF": {"recuperation_gear_adv": 0, "power": False}}
    return coordinator


@pytest.fixture
def mock_api():
    """Create a mock API."""
    api = MagicMock()
    api.send = AsyncMock()
    return api


def test_fan_supported_features(mock_coordinator, mock_api):
    """Test that fan entity supports TURN_ON, TURN_OFF, and SET_SPEED."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    
    # Check supported features
    assert fan.supported_features & FanEntityFeature.SET_SPEED
    assert fan.supported_features & FanEntityFeature.TURN_ON
    assert fan.supported_features & FanEntityFeature.TURN_OFF


def test_fan_has_turn_on_method(mock_coordinator, mock_api):
    """Test that fan entity has async_turn_on method."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    
    # Check method exists
    assert hasattr(fan, "async_turn_on")
    assert callable(fan.async_turn_on)


def test_fan_has_turn_off_method(mock_coordinator, mock_api):
    """Test that fan entity has async_turn_off method."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    
    # Check method exists
    assert hasattr(fan, "async_turn_off")
    assert callable(fan.async_turn_off)


def test_fan_extra_state_attributes(mock_coordinator, mock_api):
    """Test that fan entity provides extra state attributes."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    
    attrs = fan.extra_state_attributes
    assert "last_percentage" in attrs


@pytest.mark.asyncio
async def test_fan_turn_off(mock_coordinator, mock_api):
    """Test fan turn_off sends correct command."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    fan.async_write_ha_state = MagicMock()
    
    await fan.async_turn_off()
    
    mock_api.send.assert_any_call(
        "AA:BB:CC:DD:EE:FF",
        {"act": "send_power_off"},
    )


@pytest.mark.asyncio
async def test_fan_set_percentage(mock_coordinator, mock_api):
    """Test fan set_percentage sends correct command."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    fan.async_write_ha_state = MagicMock()
    
    # Set to 50% (gear 2)
    await fan.async_set_percentage(50)
    
    # Check API was called with correct commands (power on, then set gear)
    assert mock_api.send.call_count == 2
    mock_api.send.assert_any_call("AA:BB:CC:DD:EE:FF", {"act": "send_power_on"})
    mock_api.send.assert_any_call("AA:BB:CC:DD:EE:FF", {"act": "send_gear_number", "gear_nr": 2})
    
    # Check last_percentage was stored
    assert fan._last_percentage == 50


@pytest.mark.asyncio
async def test_fan_set_percentage_gear_1(mock_coordinator, mock_api):
    """Test setting fan to gear 1 (33%)."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    fan.async_write_ha_state = MagicMock()

    # Set to 33% (gear 1)
    await fan.async_set_percentage(33)
    
    assert mock_api.send.call_count == 2
    mock_api.send.assert_any_call("AA:BB:CC:DD:EE:FF", {"act": "send_power_on"})
    mock_api.send.assert_any_call("AA:BB:CC:DD:EE:FF", {"act": "send_gear_number", "gear_nr": 1})


@pytest.mark.asyncio
async def test_fan_turn_on_with_percentage(mock_coordinator, mock_api):
    """Test fan turn_on with percentage delegates to set_percentage."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    fan.async_write_ha_state = MagicMock()
    
    await fan.async_turn_on(percentage=66)
    
    # Check API was called with correct gear for 66% (and power_on)
    assert mock_api.send.call_count == 2
    mock_api.send.assert_any_call("AA:BB:CC:DD:EE:FF", {"act": "send_power_on"})
    mock_api.send.assert_any_call("AA:BB:CC:DD:EE:FF", {"act": "send_gear_number", "gear_nr": 2})


@pytest.mark.asyncio
async def test_fan_turn_on_uses_last_percentage(mock_coordinator, mock_api):
    """Test fan turn_on without percentage uses last saved percentage."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    fan.async_write_ha_state = MagicMock()
    
    # First set to 75%
    await fan.async_set_percentage(75)
    mock_api.reset_mock()
    
    # Now turn on without percentage - should use last 75%
    await fan.async_turn_on()
    
    # Check API was called (power on and set gear)
    assert mock_api.send.call_count == 2
    mock_api.send.assert_any_call("AA:BB:CC:DD:EE:FF", {"act": "send_power_on"})
    mock_api.send.assert_any_call("AA:BB:CC:DD:EE:FF", {"act": "send_gear_number", "gear_nr": 2})

@pytest.mark.asyncio
async def test_fan_percentage_property(mock_coordinator, mock_api):
    """Test that percentage property returns correct value based on gear."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    
    # Mock gear 1 in coordinator
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["recuperation_gear_adv"] = 1
    assert fan.percentage == 33

def test_fan_is_on_missing_data(mock_coordinator, mock_api):
    """Test that is_on property returns None if data is missing."""
    mock_coordinator.data = {}
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    assert fan.is_on is None

def test_fan_percentage_missing_data(mock_coordinator, mock_api):
    """Test that percentage property returns None if data is missing."""
    mock_coordinator.data = {}
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    assert fan.percentage is None


@pytest.mark.asyncio
async def test_fan_set_percentage_is_optimistic_before_device_confirms(mock_coordinator, mock_api):
    """Regression test: HA should show the requested speed immediately,
    not "off", while waiting for the device to echo the new state back
    over the websocket (this used to require clicking the speed twice)."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    fan.async_write_ha_state = MagicMock()

    # Urzadzenie w coordinatorze wciaz pokazuje stary stan (wylaczony) -
    # tak jak tuz po wyslaniu komendy, zanim przyjdzie echo z WebSocket.
    await fan.async_set_percentage(66)

    assert fan.is_on is True
    assert fan.percentage == 66
    fan.async_write_ha_state.assert_called()


@pytest.mark.asyncio
async def test_fan_optimistic_state_cleared_once_device_confirms(mock_coordinator, mock_api):
    """Once the coordinator receives an authoritative update, it should win
    over the optimistic guess (and not get stuck showing a stale value)."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    fan.async_write_ha_state = MagicMock()
    fan.async_on_remove = MagicMock()

    await fan.async_set_percentage(66)
    assert fan.percentage == 66  # optimistic

    # Urzadzenie potwierdza inny bieg niz zakladalismy optymistycznie.
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"] = {"power": True, "recuperation_gear_adv": 1}
    fan._handle_coordinator_update()

    assert fan.is_on is True
    assert fan.percentage == 33


@pytest.mark.asyncio
async def test_fan_turn_off_is_optimistic(mock_coordinator, mock_api):
    """turn_off should also reflect immediately in HA, not just on the device."""
    fan = AwentaFan(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Fan")
    fan.async_write_ha_state = MagicMock()

    await fan.async_turn_off()

    assert fan.is_on is False
    assert fan.percentage == 0
