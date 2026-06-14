import pytest
<<<<<<< HEAD
from unittest.mock import AsyncMock, patch, MagicMock
=======
from unittest.mock import patch, MagicMock
>>>>>>> 81bedee (🧪 Add tests for login method in AwentaAPI)
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from awenta_ahr.awenta_api import AwentaAPI

<<<<<<< HEAD
@pytest.mark.asyncio
async def test_login_failure():
    hass = MagicMock()
    api = AwentaAPI(hass, "test@test.com", "password")

    # Create mock session and response
    mock_response = AsyncMock()
    mock_response.text.return_value = json.dumps({"success": False, "msg": "Error"})

    mock_session = MagicMock()
    # async with session.post() as resp:
    mock_session.post.return_value.__aenter__.return_value = mock_response

    with patch("awenta_ahr.awenta_api.async_get_clientsession", return_value=mock_session):
        with pytest.raises(Exception, match="Login failed: Error"):
            await api.login()
=======
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
>>>>>>> 81bedee (🧪 Add tests for login method in AwentaAPI)
