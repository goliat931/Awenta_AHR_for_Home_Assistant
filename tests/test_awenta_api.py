import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from awenta_ahr.awenta_api import AwentaAPI

@pytest.fixture
def mock_hass():
    hass = MagicMock()
    return hass

class ResponseMock:
    def __init__(self, text_return_value):
        self.text_return_value = text_return_value

    async def text(self):
        return self.text_return_value

class AsyncContextManagerMock:
    def __init__(self, text_return_value):
        self.text_return_value = text_return_value

    async def __aenter__(self):
        return ResponseMock(self.text_return_value)

    async def __aexit__(self, exc_type, exc, tb):
        pass

@pytest.mark.asyncio
@patch('awenta_ahr.awenta_api.async_get_clientsession')
async def test_awenta_api_login_success(mock_get_session, mock_hass):
    """Test successful login."""

    mock_session = MagicMock()
    mock_session.post.return_value = AsyncContextManagerMock(
        json.dumps({
            "success": True,
            "params": {
                "id": 123,
                "key": "test_key"
            }
        })
    )
    mock_get_session.return_value = mock_session

    api = AwentaAPI(mock_hass, "test@example.com", "password123")
    await api.login()

    assert api.id_socket == 123
    assert api.key_socket == "test_key"

@pytest.mark.asyncio
@patch('awenta_ahr.awenta_api.async_get_clientsession')
async def test_awenta_api_login_failed(mock_get_session, mock_hass):
    """Test failed login raises exception."""

    mock_session = MagicMock()
    mock_session.post.return_value = AsyncContextManagerMock(
        json.dumps({
            "success": False,
            "msg": "Invalid credentials"
        })
    )
    mock_get_session.return_value = mock_session

    api = AwentaAPI(mock_hass, "test@example.com", "password123")

    with pytest.raises(Exception, match="Login failed: Invalid credentials"):
        await api.login()

@pytest.mark.asyncio
@patch('awenta_ahr.awenta_api.async_get_clientsession')
async def test_awenta_api_login_no_key(mock_get_session, mock_hass):
    """Test login missing key socket raises exception."""

    mock_session = MagicMock()
    mock_session.post.return_value = AsyncContextManagerMock(
        json.dumps({
            "success": True,
            "params": {
                "id": 123
            }
        })
    )
    mock_get_session.return_value = mock_session

    api = AwentaAPI(mock_hass, "test@example.com", "password123")

    with pytest.raises(Exception, match="No socket key received"):
        await api.login()

@pytest.mark.asyncio
@patch('awenta_ahr.awenta_api.async_get_clientsession')
async def test_awenta_api_login_id_socket_fallback(mock_get_session, mock_hass):
    """Test login handles 'id_socket' key fallback."""

    mock_session = MagicMock()
    mock_session.post.return_value = AsyncContextManagerMock(
        json.dumps({
            "success": True,
            "params": {
                "id_socket": 456,
                "key": "test_key2"
            }
        })
    )
    mock_get_session.return_value = mock_session

    api = AwentaAPI(mock_hass, "test@example.com", "password123")
    await api.login()

    assert api.id_socket == 456
    assert api.key_socket == "test_key2"

@pytest.mark.asyncio
@patch('awenta_ahr.awenta_api.async_get_clientsession')
async def test_awenta_api_login_id_default_fallback(mock_get_session, mock_hass):
    """Test login falls back to 1 if neither id nor id_socket are present."""

    mock_session = MagicMock()
    mock_session.post.return_value = AsyncContextManagerMock(
        json.dumps({
            "success": True,
            "params": {
                "key": "test_key3"
            }
        })
    )
    mock_get_session.return_value = mock_session

    api = AwentaAPI(mock_hass, "test@example.com", "password123")
    await api.login()

    assert api.id_socket == 1
    assert api.key_socket == "test_key3"

@pytest.mark.asyncio
async def test_awenta_api_list_devices_in_devices(mock_hass):
    """Test list_devices populates devices from 'devices' key."""
    api = AwentaAPI(mock_hass, "test@example.com", "password123")

    expected_devices = [{"mac": "00:11:22:33:44:55", "name": "Awenta Fan 1"}]

    with patch.object(api, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"devices": expected_devices}

        await api.list_devices()

        mock_request.assert_called_once_with("list_devices", "{}")
        assert api.devices == expected_devices

@pytest.mark.asyncio
async def test_awenta_api_list_devices_in_params(mock_hass):
    """Test list_devices populates devices from 'params' key if 'devices' is not present."""
    api = AwentaAPI(mock_hass, "test@example.com", "password123")

    expected_devices = [{"mac": "66:77:88:99:AA:BB", "name": "Awenta Fan 2"}]

    with patch.object(api, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"params": expected_devices}

        await api.list_devices()

        mock_request.assert_called_once_with("list_devices", "{}")
        assert api.devices == expected_devices

@pytest.mark.asyncio
async def test_awenta_api_list_devices_empty(mock_hass):
    """Test list_devices handles empty response gracefully."""
    api = AwentaAPI(mock_hass, "test@example.com", "password123")

    with patch.object(api, '_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {}

        await api.list_devices()

        mock_request.assert_called_once_with("list_devices", "{}")
        assert api.devices == []


def test_is_connected_defaults_to_false(mock_hass):
    api = AwentaAPI(mock_hass, "test@example.com", "password123")
    assert api.is_connected("AA:BB:CC:DD:EE:FF") is False


@pytest.mark.asyncio
async def test_stop_cancels_tasks_and_closes_sockets(mock_hass):
    import asyncio

    api = AwentaAPI(mock_hass, "test@example.com", "password123")
    task = asyncio.ensure_future(asyncio.sleep(3600))
    api._tasks.append(task)
    ws = MagicMock()
    ws.close = AsyncMock()
    api.ws["AA:BB:CC:DD:EE:FF"] = ws
    api._connected.add("AA:BB:CC:DD:EE:FF")

    await api.stop()

    assert task.cancelled()
    ws.close.assert_awaited_once()
    assert api.ws == {}
    assert api.is_connected("AA:BB:CC:DD:EE:FF") is False


@pytest.mark.asyncio
@patch('awenta_ahr.awenta_api.async_get_clientsession')
async def test_login_failure_raises_auth_error(mock_get_session, mock_hass):
    from awenta_ahr.awenta_api import AwentaAuthError

    mock_session = MagicMock()
    mock_session.post.return_value = AsyncContextManagerMock(
        json.dumps({"success": False, "msg": "bad"})
    )
    mock_get_session.return_value = mock_session

    api = AwentaAPI(mock_hass, "test@example.com", "password123")
    with pytest.raises(AwentaAuthError):
        await api.login()


@pytest.mark.asyncio
@patch('awenta_ahr.awenta_api.async_get_clientsession')
async def test_non_json_response_raises_connection_error(mock_get_session, mock_hass):
    from awenta_ahr.awenta_api import AwentaConnectionError

    mock_session = MagicMock()
    mock_session.post.return_value = AsyncContextManagerMock("<html>502</html>")
    mock_get_session.return_value = mock_session

    api = AwentaAPI(mock_hass, "test@example.com", "password123")
    with pytest.raises(AwentaConnectionError):
        await api.login()
