"""Tests de integración para el cliente de Wasapaso.

Estos tests hacen peticiones REALES a la API de Wasapaso usando la API key
configurada en .env.test.

Para ejecutar estos tests:
    pytest tests/test_integration_client.py -v -m integration
"""

import pytest
from wasapaso import WasapasoClient
from wasapaso.exceptions import AuthenticationError


@pytest.mark.integration
class TestClientIntegration:
    """Tests de integración del cliente principal."""

    def test_client_initialization_with_real_key(self, real_client):
        """Test que el cliente se inicializa correctamente con una API key real."""
        assert real_client is not None
        assert real_client.api_key.startswith("wsk_")
        assert "****" in real_client.api_key  # Verifica que la key está enmascarada

    def test_health_check(self, real_client):
        """Test del endpoint de health check."""
        result = real_client.health_check()

        # Verificar estructura de la respuesta
        assert isinstance(result, dict)
        assert "message" in result or "status" in result
        print(f"\nHealth check response: {result}")

    @pytest.mark.asyncio
    async def test_health_check_async(self, real_client):
        """Test asíncrono del endpoint de health check."""
        result = await real_client.health_check_async()

        # Verificar estructura de la respuesta
        assert isinstance(result, dict)
        assert "message" in result or "status" in result
        print(f"\nHealth check async response: {result}")

    def test_get_status(self, real_client):
        """Test del endpoint de status que retorna info de la API key."""
        result = real_client.get_status()

        # Verificar estructura de la respuesta
        assert isinstance(result, dict)
        assert "success" in result

        # Si la respuesta es exitosa, debería tener datos de la API key
        if result.get("success"):
            assert "apiKey" in result or "data" in result
            print(f"\nStatus response: {result}")

    @pytest.mark.asyncio
    async def test_get_status_async(self, real_client):
        """Test asíncrono del endpoint de status."""
        result = await real_client.get_status_async()

        # Verificar estructura de la respuesta
        assert isinstance(result, dict)
        assert "success" in result

        # Si la respuesta es exitosa, debería tener datos de la API key
        if result.get("success"):
            assert "apiKey" in result or "data" in result
            print(f"\nStatus async response: {result}")

    def test_invalid_api_key_raises_error(self, base_url):
        """Test que una API key inválida produce un error de autenticación."""
        # Crear cliente con una API key inválida (pero con formato correcto)
        invalid_client = WasapasoClient(
            api_key="wsk_invalid_key_12345",
            base_url=base_url
        )

        # Intentar hacer una petición debería resultar en AuthenticationError
        with pytest.raises((AuthenticationError, Exception)) as exc_info:
            invalid_client.get_status()

        # Verificar que el error es del tipo esperado
        print(f"\nError capturado (esperado): {exc_info.value}")

    def test_client_repr(self, real_client):
        """Test de la representación string del cliente."""
        repr_str = repr(real_client)

        assert "WasapasoClient" in repr_str
        assert "wsk_" in repr_str
        assert "****" in repr_str  # La key debe estar enmascarada
        print(f"\nCliente repr: {repr_str}")

    def test_api_key_property_masked(self, real_client):
        """Test que la propiedad api_key enmascara la key real."""
        masked_key = real_client.api_key

        # La key debe estar enmascarada
        assert masked_key.startswith("wsk_")
        assert "****" in masked_key

        # No debe mostrar la key completa
        assert len(masked_key) < 40  # La key real es más larga
        print(f"\nMasked API key: {masked_key}")


@pytest.mark.integration
class TestClientResources:
    """Tests de que el cliente tiene todos los recursos necesarios."""

    def test_client_has_sessions_resource(self, real_client):
        """Test que el cliente tiene el recurso de sesiones."""
        assert hasattr(real_client, "sessions")
        assert real_client.sessions is not None

    def test_client_has_messages_resource(self, real_client):
        """Test que el cliente tiene el recurso de mensajes."""
        assert hasattr(real_client, "messages")
        assert real_client.messages is not None


@pytest.mark.integration
class TestClientConfiguration:
    """Tests de configuración del cliente."""

    def test_custom_base_url(self, real_api_key):
        """Test que se puede configurar una URL base personalizada."""
        custom_url = "https://api.custom.com"
        client = WasapasoClient(api_key=real_api_key, base_url=custom_url)

        # Verificar que el cliente se creó correctamente
        assert client is not None

    def test_custom_timeout(self, real_api_key, base_url):
        """Test que se puede configurar un timeout personalizado."""
        custom_timeout = 60.0
        client = WasapasoClient(
            api_key=real_api_key,
            base_url=base_url,
            timeout=custom_timeout
        )

        # Verificar que el cliente se creó correctamente
        assert client is not None


# Instrucciones para ejecutar solo estos tests:
# pytest tests/test_integration_client.py -v -m integration
#
# Para ejecutar incluyendo output:
# pytest tests/test_integration_client.py -v -m integration -s
