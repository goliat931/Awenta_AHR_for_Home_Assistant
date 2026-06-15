import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from awenta_ahr.awenta_api import AwentaAPI

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
