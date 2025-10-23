"""Tests de manejo de errores y excepciones del SDK.

Este archivo prueba cómo el SDK maneja diferentes códigos de error
HTTP y convierte las respuestas en las excepciones apropiadas.
"""

import pytest
import respx
import httpx
from wasapaso import WasapasoClient
from wasapaso.exceptions import (
    WasapasoError,
    AuthenticationError,
    ValidationError,
    PermissionError,
    NotFoundError,
    RateLimitError,
    ServerError,
)


@pytest.fixture
def client():
    """Fixture del cliente de Wasapaso."""
    return WasapasoClient(api_key="wsk_test_key_1234567890abcdef")


@pytest.mark.unit
class TestAuthenticationErrors:
    """Tests de errores de autenticación."""

    @respx.mock
    def test_401_authentication_error(self, client):
        """Test que un 401 genera AuthenticationError."""
        error_response = {
            "success": False,
            "message": "Invalid API key",
            "error": "AUTHENTICATION_FAILED"
        }

        respx.get("https://api.wasapaso.com/api/v1/status").mock(
            return_value=httpx.Response(401, json=error_response)
        )

        with pytest.raises(AuthenticationError) as exc_info:
            client.get_status()

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value)

    @respx.mock
    def test_401_expired_key(self, client):
        """Test con API key expirada."""
        error_response = {
            "success": False,
            "message": "API key has expired",
            "error": "KEY_EXPIRED"
        }

        respx.get("https://api.wasapaso.com/api/v1/sessions").mock(
            return_value=httpx.Response(401, json=error_response)
        )

        with pytest.raises(AuthenticationError) as exc_info:
            client.sessions.list()

        assert "expired" in str(exc_info.value).lower()


@pytest.mark.unit
class TestValidationErrors:
    """Tests de errores de validación."""

    @respx.mock
    def test_400_validation_error(self, client):
        """Test que un 400 genera ValidationError."""
        error_response = {
            "success": False,
            "message": "Missing required field: name",
            "error": "VALIDATION_ERROR"
        }

        respx.post("https://api.wasapaso.com/api/v1/sessions").mock(
            return_value=httpx.Response(400, json=error_response)
        )

        with pytest.raises(ValidationError) as exc_info:
            client.sessions.create({})

        assert exc_info.value.status_code == 400
        assert "required field" in str(exc_info.value).lower()

    @respx.mock
    def test_422_unprocessable_entity(self, client):
        """Test que un 422 también genera ValidationError."""
        error_response = {
            "success": False,
            "message": "Invalid phone number format",
            "error": "INVALID_FORMAT"
        }

        respx.post("https://api.wasapaso.com/api/v1/messages/text").mock(
            return_value=httpx.Response(422, json=error_response)
        )

        with pytest.raises(ValidationError) as exc_info:
            client.messages.send_text(
                session_id="test_session",
                to="invalid_number",
                message="Test"
            )

        assert exc_info.value.status_code == 422


@pytest.mark.unit
class TestPermissionErrors:
    """Tests de errores de permisos."""

    @respx.mock
    def test_403_permission_error(self, client):
        """Test que un 403 genera PermissionError."""
        error_response = {
            "success": False,
            "message": "API key lacks permission: sessions:delete",
            "error": "PERMISSION_DENIED"
        }

        respx.delete("https://api.wasapaso.com/api/v1/sessions/test123").mock(
            return_value=httpx.Response(403, json=error_response)
        )

        with pytest.raises(PermissionError) as exc_info:
            client.sessions.delete("test123")

        assert exc_info.value.status_code == 403
        assert "permission" in str(exc_info.value).lower()


@pytest.mark.unit
class TestNotFoundErrors:
    """Tests de errores 404."""

    @respx.mock
    def test_404_session_not_found(self, client):
        """Test que un 404 genera NotFoundError."""
        error_response = {
            "success": False,
            "message": "Session not found",
            "error": "NOT_FOUND"
        }

        respx.get("https://api.wasapaso.com/api/v1/sessions/nonexistent").mock(
            return_value=httpx.Response(404, json=error_response)
        )

        with pytest.raises(NotFoundError) as exc_info:
            client.sessions.get("nonexistent")

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value).lower()

    @respx.mock
    def test_404_message_not_found(self, client):
        """Test 404 al buscar mensaje inexistente."""
        error_response = {
            "success": False,
            "message": "Message not found",
            "error": "NOT_FOUND"
        }

        respx.get("https://api.wasapaso.com/api/v1/messages/msg_fake").mock(
            return_value=httpx.Response(404, json=error_response)
        )

        with pytest.raises(NotFoundError) as exc_info:
            client.messages.get("msg_fake")

        assert "Message not found" in str(exc_info.value)


@pytest.mark.unit
class TestRateLimitErrors:
    """Tests de errores de límite de tasa."""

    @respx.mock
    def test_429_rate_limit_error(self, client):
        """Test que un 429 genera RateLimitError."""
        error_response = {
            "success": False,
            "message": "Rate limit exceeded. Try again in 60 seconds.",
            "error": "RATE_LIMIT_EXCEEDED",
            "retryAfter": 60
        }

        respx.post("https://api.wasapaso.com/api/v1/messages/text").mock(
            return_value=httpx.Response(429, json=error_response)
        )

        with pytest.raises(RateLimitError) as exc_info:
            client.messages.send_text(
                session_id="test",
                to="1234567890",
                message="Test"
            )

        assert exc_info.value.status_code == 429
        assert "rate limit" in str(exc_info.value).lower()


@pytest.mark.unit
class TestServerErrors:
    """Tests de errores del servidor."""

    @respx.mock
    def test_500_internal_server_error(self, client):
        """Test que un 500 genera ServerError."""
        error_response = {
            "success": False,
            "message": "Internal server error",
            "error": "INTERNAL_ERROR"
        }

        respx.get("https://api.wasapaso.com/api/v1/sessions").mock(
            return_value=httpx.Response(500, json=error_response)
        )

        with pytest.raises(ServerError) as exc_info:
            client.sessions.list()

        assert exc_info.value.status_code == 500

    @respx.mock
    def test_503_service_unavailable(self, client):
        """Test que un 503 genera ServerError."""
        error_response = {
            "success": False,
            "message": "Service temporarily unavailable",
            "error": "SERVICE_UNAVAILABLE"
        }

        respx.get("https://api.wasapaso.com/api/v1/health").mock(
            return_value=httpx.Response(503, json=error_response)
        )

        with pytest.raises(ServerError) as exc_info:
            client.health_check()

        assert exc_info.value.status_code == 503


@pytest.mark.unit
class TestGenericErrors:
    """Tests de errores genéricos."""

    @respx.mock
    def test_unknown_status_code(self, client):
        """Test que códigos desconocidos generan WasapasoError genérico."""
        error_response = {
            "success": False,
            "message": "Something went wrong",
            "error": "UNKNOWN_ERROR"
        }

        respx.get("https://api.wasapaso.com/api/v1/status").mock(
            return_value=httpx.Response(418, json=error_response)  # I'm a teapot
        )

        with pytest.raises(WasapasoError) as exc_info:
            client.get_status()

        assert exc_info.value.status_code == 418

    @respx.mock
    def test_error_response_data_available(self, client):
        """Test que los datos de la respuesta están disponibles en la excepción."""
        error_response = {
            "success": False,
            "message": "Validation failed",
            "error": "VALIDATION_ERROR",
            "details": {
                "field": "phoneNumber",
                "issue": "Invalid format"
            }
        }

        respx.post("https://api.wasapaso.com/api/v1/sessions/test/pair").mock(
            return_value=httpx.Response(400, json=error_response)
        )

        with pytest.raises(ValidationError) as exc_info:
            client.sessions.request_pairing_code("test", "invalid")

        # Verificar que response_data está disponible
        assert exc_info.value.response_data is not None
        assert "details" in exc_info.value.response_data


@pytest.mark.unit
@pytest.mark.asyncio
class TestAsyncErrorHandling:
    """Tests de manejo de errores en métodos async."""

    @respx.mock
    async def test_async_authentication_error(self, client):
        """Test de AuthenticationError en método async."""
        error_response = {
            "success": False,
            "message": "Invalid API key"
        }

        respx.get("https://api.wasapaso.com/api/v1/status").mock(
            return_value=httpx.Response(401, json=error_response)
        )

        with pytest.raises(AuthenticationError):
            await client.get_status_async()

    @respx.mock
    async def test_async_not_found_error(self, client):
        """Test de NotFoundError en método async."""
        error_response = {
            "success": False,
            "message": "Session not found"
        }

        respx.get("https://api.wasapaso.com/api/v1/sessions/fake").mock(
            return_value=httpx.Response(404, json=error_response)
        )

        with pytest.raises(NotFoundError):
            await client.sessions.get_async("fake")

    @respx.mock
    async def test_async_validation_error(self, client):
        """Test de ValidationError en método async."""
        error_response = {
            "success": False,
            "message": "Missing required fields"
        }

        respx.post("https://api.wasapaso.com/api/v1/sessions").mock(
            return_value=httpx.Response(400, json=error_response)
        )

        with pytest.raises(ValidationError):
            await client.sessions.create_async({})


@pytest.mark.unit
class TestErrorMessageFormatting:
    """Tests de formato de mensajes de error."""

    def test_error_string_representation(self):
        """Test de representación en string de errores."""
        error = WasapasoError("Test error", status_code=400)

        error_str = str(error)
        assert "[400]" in error_str
        assert "Test error" in error_str

    def test_error_repr(self):
        """Test de __repr__ de errores."""
        error = AuthenticationError("Auth failed", status_code=401)

        error_repr = repr(error)
        assert "AuthenticationError" in error_repr
        assert "401" in error_repr

    def test_error_without_status_code(self):
        """Test de error sin código de estado."""
        error = WasapasoError("Connection timeout")

        error_str = str(error)
        assert "Connection timeout" in error_str
        assert "[" not in error_str  # No debe tener corchetes sin status code


# Instrucciones para ejecutar:
# pytest tests/test_error_handling.py -v
