import pytest
from unittest.mock import MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTime
from awenta_ahr.sensor import (
    AwentaTemperatureSensor,
    AwentaHumiditySensor,
    AwentaFilterTimeLeftSensor,
    async_setup_entry,
)
from awenta_ahr.const import DOMAIN


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "AA:BB:CC:DD:EE:FF": {
            "data_valid": True,
            "valid_sensor": True,
            "temperature_sensor": 21.5,
            "humidity_sensor": 45
        }
    }
    return coordinator


@pytest.fixture
def mock_api():
    """Create a mock API."""
    api = MagicMock()
    api.devices = [{"mac": "AA:BB:CC:DD:EE:FF", "name": "Test Device"}]
    return api


@pytest.fixture
def mock_hass(mock_coordinator, mock_api):
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {
        DOMAIN: {
            "test_entry_id": {
                "api": mock_api,
                "coordinator": mock_coordinator
            }
        }
    }
    return hass

def test_temperature_sensor_properties(mock_coordinator, mock_api):
    """Test initialization properties of the temperature sensor."""
    sensor = AwentaTemperatureSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.has_entity_name is True
    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.unique_id == "AA:BB:CC:DD:EE:FF_temperature"
    assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS

def test_temperature_sensor_native_value_valid(mock_coordinator, mock_api):
    """Test native_value returns temperature when data is valid."""
    sensor = AwentaTemperatureSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value == 21.5

def test_temperature_sensor_native_value_invalid_data(mock_coordinator, mock_api):
    """Test native_value returns None when data_valid is false."""
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["data_valid"] = False
    sensor = AwentaTemperatureSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value is None

def test_temperature_sensor_native_value_invalid_sensor(mock_coordinator, mock_api):
    """Test native_value returns None when valid_sensor is false."""
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["valid_sensor"] = False
    sensor = AwentaTemperatureSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value is None

def test_temperature_sensor_native_value_no_data(mock_coordinator, mock_api):
    """Test native_value returns None when mac is missing from coordinator data."""
    mock_coordinator.data = {}
    sensor = AwentaTemperatureSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value is None

def test_temperature_sensor_native_value_missing_valid_sensor(mock_coordinator, mock_api):
    """Test native_value returns temperature when valid_sensor is missing but data_valid is true."""
    del mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["valid_sensor"]
    sensor = AwentaTemperatureSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value == 21.5

def test_humidity_sensor_properties(mock_coordinator, mock_api):
    """Test initialization properties of the humidity sensor."""
    sensor = AwentaHumiditySensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.has_entity_name is True
    assert sensor.device_class == SensorDeviceClass.HUMIDITY
    assert sensor.unique_id == "AA:BB:CC:DD:EE:FF_humidity"
    assert sensor.native_unit_of_measurement == PERCENTAGE

def test_humidity_sensor_native_value_valid(mock_coordinator, mock_api):
    """Test native_value returns humidity when data is valid."""
    sensor = AwentaHumiditySensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value == 45

def test_humidity_sensor_native_value_invalid_data(mock_coordinator, mock_api):
    """Test native_value returns None when data_valid is false."""
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["data_valid"] = False
    sensor = AwentaHumiditySensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value is None

def test_humidity_sensor_native_value_invalid_sensor(mock_coordinator, mock_api):
    """Test native_value returns None when valid_sensor is false."""
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["valid_sensor"] = False
    sensor = AwentaHumiditySensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value is None

def test_humidity_sensor_native_value_no_data(mock_coordinator, mock_api):
    """Test native_value returns None when mac is missing from coordinator data."""
    mock_coordinator.data = {}
    sensor = AwentaHumiditySensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value is None

def test_humidity_sensor_native_value_missing_valid_sensor(mock_coordinator, mock_api):
    """Test native_value returns humidity when valid_sensor is missing but data_valid is true."""
    del mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["valid_sensor"]
    sensor = AwentaHumiditySensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value == 45

@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass, mock_coordinator, mock_api):
    """Test that setup entry creates the correct entities."""
    # Create mock entry
    entry = MagicMock()
    entry.entry_id = "test_entry_id"

    # Create mock add_entities callback
    async_add_entities = MagicMock()

    # Run setup
    await async_setup_entry(mock_hass, entry, async_add_entities)

    # Verify entities were added
    async_add_entities.assert_called_once()

    # Get the list of entities passed to the callback
    entities = async_add_entities.call_args[0][0]

    # 3 entities per device: temperature, humidity, filter time left
    assert len(entities) == 3

    # Verify the first entity is a Temperature Sensor
    assert isinstance(entities[0], AwentaTemperatureSensor)
    assert entities[0].unique_id == "AA:BB:CC:DD:EE:FF_temperature"

    # Verify the second entity is a Humidity Sensor
    assert isinstance(entities[1], AwentaHumiditySensor)
    assert entities[1].unique_id == "AA:BB:CC:DD:EE:FF_humidity"

    assert isinstance(entities[2], AwentaFilterTimeLeftSensor)
    assert entities[2].unique_id == "AA:BB:CC:DD:EE:FF_filter_time_left"

@pytest.mark.asyncio
async def test_async_setup_entry_multiple_devices(mock_hass, mock_coordinator, mock_api):
    """Test setup entry with multiple devices."""
    # Add a second device to the API
    mock_api.devices.append({"mac": "11:22:33:44:55:66", "name": "Second Device"})

    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    async_add_entities = MagicMock()

    await async_setup_entry(mock_hass, entry, async_add_entities)

    entities = async_add_entities.call_args[0][0]

    assert len(entities) == 6

    # Check that devices have the correct types and properties
    sensor_types = [type(e) for e in entities]
    assert sensor_types == [
        AwentaTemperatureSensor,
        AwentaHumiditySensor,
        AwentaFilterTimeLeftSensor,
        AwentaTemperatureSensor,
        AwentaHumiditySensor,
        AwentaFilterTimeLeftSensor,
    ]

    assert entities[3].unique_id == "11:22:33:44:55:66_temperature"
    assert entities[4].unique_id == "11:22:33:44:55:66_humidity"


def test_filter_sensor_properties(mock_coordinator, mock_api):
    sensor = AwentaFilterTimeLeftSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.unique_id == "AA:BB:CC:DD:EE:FF_filter_time_left"
    assert sensor.translation_key == "filter_time_left"
    assert sensor.device_class == SensorDeviceClass.DURATION
    assert sensor.native_unit_of_measurement == UnitOfTime.HOURS


def test_filter_sensor_value_in_hours(mock_coordinator, mock_api):
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["time_filter_time_left"] = 2160
    sensor = AwentaFilterTimeLeftSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value == 2160
    assert sensor.extra_state_attributes == {"days_left": 90.0}


def test_filter_sensor_never_negative(mock_coordinator, mock_api):
    mock_coordinator.data["AA:BB:CC:DD:EE:FF"]["time_filter_time_left"] = -5
    sensor = AwentaFilterTimeLeftSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value == 0


def test_filter_sensor_missing_value(mock_coordinator, mock_api):
    sensor = AwentaFilterTimeLeftSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    assert sensor.native_value is None
    assert sensor.extra_state_attributes is None


def test_entity_unavailable_when_websocket_disconnected(mock_coordinator, mock_api):
    sensor = AwentaFilterTimeLeftSensor(mock_coordinator, mock_api, "AA:BB:CC:DD:EE:FF", "Test Device")

    mock_api.is_connected.return_value = True
    assert sensor.available is True

    mock_api.is_connected.return_value = False
    assert sensor.available is False


def test_entity_unavailable_without_any_data(mock_coordinator, mock_api):
    mock_api.is_connected.return_value = True
    sensor = AwentaFilterTimeLeftSensor(mock_coordinator, mock_api, "11:22:33:44:55:66", "Other")

    assert sensor.available is False
