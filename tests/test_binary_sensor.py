import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from awenta_ahr.binary_sensor import AwentaFilterReplaceBinarySensor, async_setup_entry
from awenta_ahr.const import DOMAIN

MAC = "AA:BB:CC:DD:EE:FF"


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.data = {MAC: {"data_valid": True}}
    return coordinator


@pytest.fixture
def mock_api():
    api = MagicMock()
    api.devices = [{"mac": MAC, "name": "Test Device"}]
    return api


def _sensor(coordinator, api):
    return AwentaFilterReplaceBinarySensor(coordinator, api, MAC, "Test Device")


def test_properties(mock_coordinator, mock_api):
    sensor = _sensor(mock_coordinator, mock_api)
    assert sensor.unique_id == f"{MAC}_filter_replace"
    assert sensor.translation_key == "filter_replace"
    assert sensor.device_class == BinarySensorDeviceClass.PROBLEM


@pytest.mark.parametrize(
    "hours, expected", [(2160, False), (1, False), (0, True), (-3, True)]
)
def test_is_on(mock_coordinator, mock_api, hours, expected):
    mock_coordinator.data[MAC]["time_filter_time_left"] = hours
    assert _sensor(mock_coordinator, mock_api).is_on is expected


def test_unknown_when_missing(mock_coordinator, mock_api):
    assert _sensor(mock_coordinator, mock_api).is_on is None


async def test_async_setup_entry(mock_coordinator, mock_api):
    hass = MagicMock()
    hass.data = {DOMAIN: {"e": {"api": mock_api, "coordinator": mock_coordinator}}}
    entry = MagicMock()
    entry.entry_id = "e"
    add = MagicMock()

    await async_setup_entry(hass, entry, add)

    entities = list(add.call_args[0][0])
    assert len(entities) == 1
    assert isinstance(entities[0], AwentaFilterReplaceBinarySensor)
