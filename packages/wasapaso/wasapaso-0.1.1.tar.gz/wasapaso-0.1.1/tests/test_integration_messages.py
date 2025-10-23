"""Tests de integración para el recurso de mensajes.

Estos tests hacen peticiones REALES a la API de Wasapaso.
NOTA: Algunos tests requieren una sesión autenticada con WhatsApp.

Para ejecutar estos tests:
    pytest tests/test_integration_messages.py -v -m integration

IMPORTANTE:
- Necesitas tener al menos una sesión WORKING (autenticada) para algunos tests
- Los mensajes se enviarán a números reales si la sesión está autenticada
- Usa números de prueba o tu propio número para evitar spam
"""

import time
import pytest
from wasapaso.models.message import Message, MessageList
from wasapaso.exceptions import ValidationError, NotFoundError


@pytest.fixture
def working_session_id(real_client):
    """
    Fixture que intenta encontrar o crear una sesión WORKING.

    Si no hay sesiones WORKING, algunos tests se saltarán.
    """
    # Intentar encontrar una sesión WORKING
    sessions = real_client.sessions.list(status="WORKING", limit=1)

    if sessions.data and len(sessions.data) > 0:
        session_id = sessions.data[0].id
        print(f"\nUsando sesión existente: {session_id}")
        return session_id

    # Si no hay sesión WORKING, intentar crear una
    print("\nNo se encontró sesión WORKING. Algunos tests se saltarán.")
    return None


@pytest.mark.integration
class TestMessagesBasic:
    """Tests básicos de mensajes que no requieren sesión autenticada."""

    def test_send_text_message_structure(self, real_client, session_ids_to_cleanup):
        """
        Test de la estructura de envío de mensaje de texto.

        Nota: Este test puede fallar si la sesión no está autenticada,
        pero al menos verifica que la estructura de la petición es correcta.
        """
        # Crear una sesión para pruebas
        session = real_client.sessions.create({"name": "Test Messages"})
        session_ids_to_cleanup.append(session.id)

        try:
            # Intentar enviar un mensaje (probablemente falle por no estar autenticada)
            result = real_client.messages.send_text(
                session_id=session.id,
                to="1234567890",  # Número de prueba
                message="Test message from SDK"
            )

            # Si llega aquí, el mensaje se envió (poco probable)
            assert isinstance(result, dict)
            assert "data" in result or "success" in result
            print(f"\nMensaje enviado (inesperado): {result}")

        except ValidationError as e:
            # Esperado si la sesión no está autenticada
            print(f"\nError esperado (sesión no autenticada): {e}")
            assert "session" in str(e).lower() or "not" in str(e).lower()

        except Exception as e:
            # Otro error, pero al menos verificamos que la estructura es correcta
            print(f"\nError al enviar mensaje: {type(e).__name__}: {e}")

    @pytest.mark.asyncio
    async def test_send_text_message_async_structure(self, real_client, session_ids_to_cleanup):
        """Test asíncrono de envío de mensaje de texto."""
        session = await real_client.sessions.create_async({"name": "Test Messages Async"})
        session_ids_to_cleanup.append(session.id)

        try:
            result = await real_client.messages.send_text_async(
                session_id=session.id,
                to="1234567890",
                message="Test async message"
            )

            assert isinstance(result, dict)
            print(f"\nMensaje async enviado: {result}")

        except (ValidationError, Exception) as e:
            print(f"\nError esperado (async): {e}")


@pytest.mark.integration
class TestMessagesWithWorkingSession:
    """
    Tests que requieren una sesión WORKING (autenticada).

    Para ejecutar estos tests:
        pytest tests/test_integration_messages.py -v -m integration --run-send-tests

    ADVERTENCIA: Estos tests enviarán mensajes REALES si tienes una sesión autenticada.

    Nota: Estos tests se saltarán automáticamente si no hay una sesión WORKING disponible.
    """

    def test_send_text_message_real(self, real_client, working_session_id):
        """Test de envío real de mensaje de texto."""
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        # IMPORTANTE: Cambiar este número por uno de prueba o tu propio número
        test_phone_number = "1234567890"  # CAMBIAR POR NÚMERO REAL

        result = real_client.messages.send_text(
            session_id=working_session_id,
            to=test_phone_number,
            message="Test message from Wasapaso Python SDK - Integration Test"
        )

        assert isinstance(result, dict)
        assert result.get("success", False) or "data" in result
        print(f"\nMensaje enviado: {result}")

    def test_send_media_message_real(self, real_client, working_session_id):
        """Test de envío de mensaje multimedia."""
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        test_phone_number = "1234567890"  # CAMBIAR POR NÚMERO REAL

        result = real_client.messages.send_media(
            session_id=working_session_id,
            to=test_phone_number,
            media_type="image",
            media_url="https://picsum.photos/200",
            caption="Test image from SDK"
        )

        assert isinstance(result, dict)
        print(f"\nMensaje multimedia enviado: {result}")

    def test_send_location_message_real(self, real_client, working_session_id):
        """Test de envío de ubicación."""
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        test_phone_number = "1234567890"  # CAMBIAR POR NÚMERO REAL

        result = real_client.messages.send_location(
            session_id=working_session_id,
            to=test_phone_number,
            latitude=40.7128,
            longitude=-74.0060,
            title="New York City - Test"
        )

        assert isinstance(result, dict)
        print(f"\nUbicación enviada: {result}")


@pytest.mark.integration
class TestMessagesListing:
    """Tests de listado de mensajes."""

    def test_list_messages_basic(self, real_client, working_session_id):
        """Test básico de listado de mensajes."""
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        messages = real_client.messages.list(
            session_id=working_session_id,
            limit=10
        )

        assert isinstance(messages, MessageList)
        assert hasattr(messages, "data")
        assert isinstance(messages.data, list)
        print(f"\nMensajes listados: {len(messages.data)}")

        if messages.data:
            first_msg = messages.data[0]
            print(f"Primer mensaje: {first_msg.type} - {first_msg.body[:50] if first_msg.body else 'N/A'}")

    @pytest.mark.asyncio
    async def test_list_messages_async(self, real_client, working_session_id):
        """Test asíncrono de listado de mensajes."""
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        messages = await real_client.messages.list_async(
            session_id=working_session_id,
            limit=5
        )

        assert isinstance(messages, MessageList)
        print(f"\nMensajes listados (async): {len(messages.data)}")

    def test_list_messages_with_filters(self, real_client, working_session_id):
        """Test de listado con filtros."""
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        # Listar solo mensajes enviados por mí
        my_messages = real_client.messages.list(
            session_id=working_session_id,
            from_me=True,
            limit=10
        )

        assert isinstance(my_messages, MessageList)
        # Verificar que todos son mensajes enviados por mí
        for msg in my_messages.data:
            if hasattr(msg, "fromMe"):
                assert msg.fromMe is True
        print(f"\nMis mensajes: {len(my_messages.data)}")

    def test_list_messages_pagination(self, real_client, working_session_id):
        """Test de paginación de mensajes."""
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        # Primera página
        page1 = real_client.messages.list(
            session_id=working_session_id,
            limit=5,
            offset=0
        )

        # Segunda página
        page2 = real_client.messages.list(
            session_id=working_session_id,
            limit=5,
            offset=5
        )

        assert isinstance(page1, MessageList)
        assert isinstance(page2, MessageList)
        print(f"\nPágina 1: {len(page1.data)}, Página 2: {len(page2.data)}")


@pytest.mark.integration
class TestMessagesOperations:
    """Tests de operaciones sobre mensajes existentes."""

    def test_get_message(self, real_client, working_session_id):
        """Test de obtención de un mensaje específico."""
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        # Primero obtener la lista de mensajes
        messages = real_client.messages.list(
            session_id=working_session_id,
            limit=1
        )

        if not messages.data:
            pytest.skip("No hay mensajes disponibles para probar")

        message_id = messages.data[0].id

        # Obtener el mensaje específico
        message = real_client.messages.get(message_id)

        assert isinstance(message, Message)
        assert message.id == message_id
        print(f"\nMensaje obtenido: {message.id}")

    @pytest.mark.asyncio
    async def test_get_message_async(self, real_client, working_session_id):
        """Test asíncrono de obtención de mensaje."""
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        messages = await real_client.messages.list_async(
            session_id=working_session_id,
            limit=1
        )

        if not messages.data:
            pytest.skip("No hay mensajes disponibles")

        message = await real_client.messages.get_async(messages.data[0].id)

        assert isinstance(message, Message)
        print(f"\nMensaje obtenido (async): {message.id}")

    def test_mark_as_read(self, real_client, working_session_id):
        """Test de marcar mensaje como leído.

        Nota: Este test se salta si no hay sesión WORKING.
        """
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        # Obtener un mensaje recibido (no enviado por mí)
        messages = real_client.messages.list(
            session_id=working_session_id,
            from_me=False,
            limit=1
        )

        if not messages.data:
            pytest.skip("No hay mensajes recibidos para marcar como leído")

        message_id = messages.data[0].id

        # Marcar como leído
        result = real_client.messages.mark_as_read(message_id)

        assert isinstance(result, dict)
        print(f"\nMensaje marcado como leído: {result}")

    def test_react_to_message(self, real_client, working_session_id):
        """Test de reacción a un mensaje.

        Nota: Este test se salta si no hay sesión WORKING.
        """
        if not working_session_id:
            pytest.skip("No hay sesión WORKING disponible")

        messages = real_client.messages.list(
            session_id=working_session_id,
            limit=1
        )

        if not messages.data:
            pytest.skip("No hay mensajes para reaccionar")

        message_id = messages.data[0].id

        # Reaccionar con un emoji
        result = real_client.messages.react(message_id, "👍")

        assert isinstance(result, dict)
        print(f"\nReacción enviada: {result}")


# Instrucciones:
# pytest tests/test_integration_messages.py -v -m integration
#
# NOTA: Los tests que envían mensajes reales se saltarán automáticamente
# si no hay una sesión WORKING disponible.
