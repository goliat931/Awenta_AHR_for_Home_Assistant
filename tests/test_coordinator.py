import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from awenta_ahr.coordinator import AwentaCoordinator


def _make_coordinator():
    # Nie wywolujemy AwentaCoordinator(hass, api) - DataUpdateCoordinator.__init__
    # poza prawdziwym Home Assistant (bez frame/config_entry z ContextVar) rzuca
    # blad w warstwie HA niezwiazany z logika, ktora testujemy. Budujemy wiec
    # instancje z pominieciem __init__, tak jak potrzebuje _handle_update.
    coordinator = AwentaCoordinator.__new__(AwentaCoordinator)
    coordinator.data = {}
    coordinator.async_set_updated_data = MagicMock()
    return coordinator


def test_handle_update_merges_instead_of_replacing():
    """Regression test: a partial websocket message (missing e.g. 'power' or
    'recuperation_gear_adv') must not wipe fields we already knew, or the
    fan entity briefly renders as off/0% right after a speed change."""
    coordinator = _make_coordinator()
    mac = "AA:BB:CC:DD:EE:FF"

    coordinator._handle_update(mac, {"power": True, "recuperation_gear_adv": 2, "mode": 1})
    assert coordinator.data[mac]["power"] is True
    assert coordinator.data[mac]["recuperation_gear_adv"] == 2

    # Kolejna, czesciowa wiadomosc (np. sam odczyt czujnika) nie powinna
    # skasowac wczesniej poznanych pol power/recuperation_gear_adv.
    coordinator._handle_update(mac, {"temperature_sensor": 21.5})

    assert coordinator.data[mac]["power"] is True
    assert coordinator.data[mac]["recuperation_gear_adv"] == 2
    assert coordinator.data[mac]["temperature_sensor"] == 21.5


def test_handle_update_overwrites_fields_present_in_new_message():
    coordinator = _make_coordinator()
    mac = "AA:BB:CC:DD:EE:FF"

    coordinator._handle_update(mac, {"power": True, "recuperation_gear_adv": 1})
    coordinator._handle_update(mac, {"power": False, "recuperation_gear_adv": 0})

    assert coordinator.data[mac]["power"] is False
    assert coordinator.data[mac]["recuperation_gear_adv"] == 0
