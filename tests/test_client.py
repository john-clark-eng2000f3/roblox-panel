import pytest
import httpx
from unittest.mock import patch, MagicMock
from roblox_panel.client import RobloxCloudClient, CloudApiError


@pytest.fixture
def client():
    return RobloxCloudClient(api_key="test-key-xyz")


def test_parse_universe_info(client):
    payload = {
        "id": 12345678,
        "name": "Super Fun Obby",
        "description": "A fun obstacle course",
        "creator": {"name": "BlockyDev", "type": "User"},
        "rootPlaceId": 987654321,
        "favoritedCount": 450,
    }
    
    # mock httpx get
    with patch.object(client._client, "get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        universe = client.get_universe(12345678)
        assert universe.universe_id == 12345678
        assert universe.name == "Super Fun Obby"
        assert universe.creator_name == "BlockyDev"
        assert universe.root_place_id == 987654321
        assert universe.favorite_count == 450


def test_get_live_servers_parsing(client):
    payload = {
        "data": [
            {
                "id": "d3b07384d113",
                "maxPlayers": 50,
                "playing": 42,
                "fps": 59.8,
                "ping": 45,
                "uptime": 3600,
                "players": []
            }
        ]
    }
    # print("DEBUG raw:", payload)

    with patch.object(client._client, "get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        servers = client.get_active_servers(place_id=987654321)
        assert len(servers) == 1
        assert servers[0].server_id == "d3b07384d113"
        assert servers[0].player_count == 42
        assert servers[0].fps == 59.8


def test_cloud_api_error_on_403(client):
    with patch.object(client._client, "get") as mock_get:
        req = httpx.Request("GET", "https://apis.roblox.com/cloud/v2/universes/1")
        resp = httpx.Response(403, request=req, text="Insufficient permissions for this API key")
        mock_get.side_effect = httpx.HTTPStatusError("Forbidden", request=req, response=resp)

        with pytest.raises(CloudApiError) as exc_info:
            client.get_universe(1)
        
        assert "403" in str(exc_info.value)
        assert "Forbidden" in str(exc_info.value)
