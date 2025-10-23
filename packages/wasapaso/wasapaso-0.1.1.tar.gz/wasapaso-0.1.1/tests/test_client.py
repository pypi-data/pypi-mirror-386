"""Tests para el cliente principal de Wasapaso."""

import pytest
import respx
import httpx
from wasapaso import WasapasoClient
from wasapaso.exceptions import WasapasoError


@pytest.mark.unit
def test_client_initialization():
    """Test de inicialización del cliente."""
    client = WasapasoClient(api_key="wsk_test_key_1234567890abcdef")
    assert client is not None
    assert "wsk_" in client.api_key


@pytest.mark.unit
def test_client_invalid_api_key_empty():
    """Test con API key vacía."""
    with pytest.raises(ValueError, match="API key is required"):
        WasapasoClient(api_key="")


@pytest.mark.unit
def test_client_invalid_api_key_format():
    """Test con formato de API key inválido."""
    with pytest.raises(ValueError, match="Invalid API key format"):
        WasapasoClient(api_key="invalid_key_format")


@pytest.mark.unit
def test_client_has_resources():
    """Test que el cliente tiene los recursos necesarios."""
    client = WasapasoClient(api_key="wsk_test_key_1234567890abcdef")
    assert hasattr(client, "sessions")
    assert hasattr(client, "messages")


@pytest.mark.unit
def test_client_repr():
    """Test de representación del cliente."""
    client = WasapasoClient(api_key="wsk_test_key_1234567890abcdef")
    repr_str = repr(client)
    assert "WasapasoClient" in repr_str
    assert "wsk_****" in repr_str


@pytest.mark.unit
@respx.mock
def test_health_check(client):
    """Test del método health_check con mock."""
    health_response = {
        "status": "ok",
        "message": "API is healthy",
        "timestamp": "2024-01-01T00:00:00.000Z"
    }

    route = respx.get("https://api.wasapaso.com/api/v1/health").mock(
        return_value=httpx.Response(200, json=health_response)
    )

    result = client.health_check()

    assert route.called
    assert isinstance(result, dict)
    assert result["status"] == "ok"
    assert "message" in result


@pytest.mark.unit
@pytest.mark.asyncio
@respx.mock
async def test_health_check_async(client):
    """Test asíncrono del método health_check."""
    health_response = {
        "status": "ok",
        "message": "API is healthy"
    }

    route = respx.get("https://api.wasapaso.com/api/v1/health").mock(
        return_value=httpx.Response(200, json=health_response)
    )

    result = await client.health_check_async()

    assert route.called
    assert isinstance(result, dict)
    assert result["status"] == "ok"


@pytest.mark.unit
@respx.mock
def test_get_status(client):
    """Test del método get_status con mock."""
    status_response = {
        "success": True,
        "apiKey": {
            "id": "key_123",
            "name": "Test API Key",
            "permissions": ["sessions:read", "sessions:write", "messages:send"],
            "rateLimit": {
                "limit": 1000,
                "remaining": 950
            }
        }
    }

    route = respx.get("https://api.wasapaso.com/api/v1/status").mock(
        return_value=httpx.Response(200, json=status_response)
    )

    result = client.get_status()

    assert route.called
    assert isinstance(result, dict)
    assert result["success"] is True
    assert "apiKey" in result
    assert result["apiKey"]["name"] == "Test API Key"


@pytest.mark.unit
@pytest.mark.asyncio
@respx.mock
async def test_get_status_async(client):
    """Test asíncrono del método get_status."""
    status_response = {
        "success": True,
        "apiKey": {
            "id": "key_123",
            "name": "Test API Key Async",
            "permissions": ["sessions:read", "messages:send"]
        }
    }

    route = respx.get("https://api.wasapaso.com/api/v1/status").mock(
        return_value=httpx.Response(200, json=status_response)
    )

    result = await client.get_status_async()

    assert route.called
    assert isinstance(result, dict)
    assert result["success"] is True
    assert result["apiKey"]["name"] == "Test API Key Async"


@pytest.mark.unit
def test_api_key_masking():
    """Test que la API key se enmascara correctamente."""
    client = WasapasoClient(api_key="wsk_test_key_1234567890abcdef")

    masked = client.api_key

    # Debe empezar con wsk_
    assert masked.startswith("wsk_")
    # Debe contener asteriscos
    assert "****" in masked
    # Debe mostrar los últimos 4 caracteres
    assert masked.endswith("cdef")


@pytest.mark.unit
def test_custom_base_url():
    """Test de cliente con URL base personalizada."""
    custom_url = "https://custom.api.com"
    client = WasapasoClient(
        api_key="wsk_test_key_1234567890abcdef",
        base_url=custom_url
    )

    assert client is not None


@pytest.mark.unit
def test_custom_timeout():
    """Test de cliente con timeout personalizado."""
    client = WasapasoClient(
        api_key="wsk_test_key_1234567890abcdef",
        timeout=60.0
    )

    assert client is not None
