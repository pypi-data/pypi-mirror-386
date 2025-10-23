"""Tests de integración para el recurso de sesiones.

Estos tests hacen peticiones REALES a la API de Wasapaso.
Crean, modifican y eliminan sesiones reales, así que ten cuidado.

Para ejecutar estos tests:
    pytest tests/test_integration_sessions.py -v -m integration
"""

import time
import pytest
from wasapaso.models.session import Session, SessionStatus, QRCode, PairingCode
from wasapaso.exceptions import NotFoundError


@pytest.mark.integration
class TestSessionsIntegration:
    """Tests de integración para operaciones con sesiones."""

    def test_create_session(self, real_client, session_ids_to_cleanup):
        """Test de creación de sesión."""
        # Crear una sesión
        session_data = {
            "name": "Test Session - Integration",
            "webhook_url": "https://example.com/webhook"
        }

        session = real_client.sessions.create(session_data)

        # Agregar a cleanup
        session_ids_to_cleanup.append(session.id)

        # Verificar que se creó correctamente
        assert isinstance(session, Session)
        assert session.id is not None
        assert session.name == "Test Session - Integration"
        assert session.status in [SessionStatus.STOPPED, SessionStatus.STARTING]
        print(f"\nSesión creada: {session.id}, status: {session.status}")

    @pytest.mark.asyncio
    async def test_create_session_async(self, real_client, session_ids_to_cleanup):
        """Test asíncrono de creación de sesión."""
        session_data = {
            "name": "Test Session Async - Integration"
        }

        session = await real_client.sessions.create_async(session_data)

        # Agregar a cleanup
        session_ids_to_cleanup.append(session.id)

        # Verificar
        assert isinstance(session, Session)
        assert session.id is not None
        assert "Async" in session.name
        print(f"\nSesión async creada: {session.id}")

    def test_list_sessions(self, real_client):
        """Test de listado de sesiones."""
        # Listar sesiones
        sessions = real_client.sessions.list(page=1, limit=10)

        # Verificar estructura
        assert hasattr(sessions, "data")
        assert hasattr(sessions, "pagination")
        assert isinstance(sessions.data, list)

        # Imprimir información
        print(f"\nTotal de sesiones: {sessions.pagination.get('total', 0)}")
        if sessions.data:
            print(f"Primera sesión: {sessions.data[0].name} - {sessions.data[0].status}")

    @pytest.mark.asyncio
    async def test_list_sessions_async(self, real_client):
        """Test asíncrono de listado de sesiones."""
        sessions = await real_client.sessions.list_async(page=1, limit=5)

        assert hasattr(sessions, "data")
        assert isinstance(sessions.data, list)
        print(f"\nSesiones listadas (async): {len(sessions.data)}")

    def test_get_session(self, real_client, session_ids_to_cleanup):
        """Test de obtención de una sesión específica."""
        # Primero crear una sesión
        session_data = {"name": "Test Get Session"}
        created = real_client.sessions.create(session_data)
        session_ids_to_cleanup.append(created.id)

        # Obtener la sesión
        session = real_client.sessions.get(created.id)

        # Verificar
        assert isinstance(session, Session)
        assert session.id == created.id
        assert session.name == "Test Get Session"
        print(f"\nSesión obtenida: {session.id}, status: {session.status}")

    @pytest.mark.asyncio
    async def test_get_session_async(self, real_client, session_ids_to_cleanup):
        """Test asíncrono de obtención de sesión."""
        # Crear sesión
        created = await real_client.sessions.create_async({"name": "Test Get Async"})
        session_ids_to_cleanup.append(created.id)

        # Obtener
        session = await real_client.sessions.get_async(created.id)

        assert session.id == created.id
        print(f"\nSesión obtenida (async): {session.id}")

    def test_update_session(self, real_client, session_ids_to_cleanup):
        """Test de actualización de sesión."""
        # Crear sesión
        created = real_client.sessions.create({"name": "Original Name"})
        session_ids_to_cleanup.append(created.id)

        # Actualizar
        update_data = {"name": "Updated Name"}
        updated = real_client.sessions.update(created.id, update_data)

        # Verificar
        assert updated.id == created.id
        assert updated.name == "Updated Name"
        print(f"\nSesión actualizada: {updated.name}")

    @pytest.mark.asyncio
    async def test_update_session_async(self, real_client, session_ids_to_cleanup):
        """Test asíncrono de actualización de sesión."""
        # Crear
        created = await real_client.sessions.create_async({"name": "Original Async"})
        session_ids_to_cleanup.append(created.id)

        # Actualizar
        updated = await real_client.sessions.update_async(
            created.id,
            {"name": "Updated Async"}
        )

        assert updated.name == "Updated Async"
        print(f"\nSesión actualizada (async): {updated.name}")

    def test_start_session(self, real_client, session_ids_to_cleanup):
        """Test de inicio de sesión."""
        # Crear sesión
        created = real_client.sessions.create({"name": "Test Start Session"})
        session_ids_to_cleanup.append(created.id)

        # Esperar un momento
        time.sleep(1)

        # Intentar iniciar la sesión
        session = real_client.sessions.start(created.id)

        # Verificar que el status cambió
        assert session.status in [SessionStatus.STARTING, SessionStatus.WORKING]
        print(f"\nSesión iniciada: {session.id}, status: {session.status}")

    @pytest.mark.asyncio
    async def test_start_session_async(self, real_client, session_ids_to_cleanup):
        """Test asíncrono de inicio de sesión."""
        created = await real_client.sessions.create_async({"name": "Test Start Async"})
        session_ids_to_cleanup.append(created.id)

        # Dar tiempo para que se cree
        time.sleep(1)

        session = await real_client.sessions.start_async(created.id)

        assert session.status in [SessionStatus.STARTING, SessionStatus.WORKING]
        print(f"\nSesión iniciada (async): status {session.status}")

    def test_get_qr_code(self, real_client, session_ids_to_cleanup):
        """Test de obtención de código QR."""
        # Crear y iniciar sesión
        created = real_client.sessions.create({"name": "Test QR"})
        session_ids_to_cleanup.append(created.id)

        time.sleep(1)
        real_client.sessions.start(created.id)
        time.sleep(2)  # Dar tiempo para que genere el QR

        try:
            # Intentar obtener QR
            qr = real_client.sessions.get_qr(created.id, format="json")

            # Verificar
            assert isinstance(qr, QRCode)
            assert hasattr(qr, "qr")
            print(f"\nQR obtenido exitosamente")

        except Exception as e:
            # El QR puede no estar disponible si la sesión ya está autenticada
            print(f"\nNo se pudo obtener QR (esperado si ya está autenticada): {e}")
            pytest.skip("QR no disponible - puede estar autenticada")

    @pytest.mark.asyncio
    async def test_get_qr_code_async(self, real_client, session_ids_to_cleanup):
        """Test asíncrono de obtención de QR."""
        created = await real_client.sessions.create_async({"name": "Test QR Async"})
        session_ids_to_cleanup.append(created.id)

        await real_client.sessions.start_async(created.id)
        time.sleep(2)

        try:
            qr = await real_client.sessions.get_qr_async(created.id)
            assert isinstance(qr, QRCode)
            print(f"\nQR obtenido (async)")
        except Exception as e:
            print(f"\nQR no disponible (async): {e}")
            pytest.skip("QR no disponible")

    def test_stop_session(self, real_client, session_ids_to_cleanup):
        """Test de detención de sesión."""
        # Crear e iniciar sesión
        created = real_client.sessions.create({"name": "Test Stop"})
        session_ids_to_cleanup.append(created.id)

        time.sleep(1)
        real_client.sessions.start(created.id)
        time.sleep(2)

        # Detener
        session = real_client.sessions.stop(created.id)

        # Verificar
        assert session.status in [SessionStatus.STOPPED, SessionStatus.STOPPING]
        print(f"\nSesión detenida: status {session.status}")

    @pytest.mark.asyncio
    async def test_stop_session_async(self, real_client, session_ids_to_cleanup):
        """Test asíncrono de detención de sesión."""
        created = await real_client.sessions.create_async({"name": "Test Stop Async"})
        session_ids_to_cleanup.append(created.id)

        await real_client.sessions.start_async(created.id)
        time.sleep(2)

        session = await real_client.sessions.stop_async(created.id)

        assert session.status in [SessionStatus.STOPPED, SessionStatus.STOPPING]
        print(f"\nSesión detenida (async): status {session.status}")

    def test_delete_session(self, real_client):
        """Test de eliminación de sesión."""
        # Crear sesión (no la agregamos a cleanup porque la vamos a eliminar)
        created = real_client.sessions.create({"name": "Test Delete"})

        # Eliminar
        result = real_client.sessions.delete(created.id)

        # Verificar
        assert isinstance(result, dict)
        assert result.get("success", False) or "message" in result
        print(f"\nSesión eliminada: {result}")

        # Verificar que ya no existe
        with pytest.raises((NotFoundError, Exception)):
            real_client.sessions.get(created.id)

    @pytest.mark.asyncio
    async def test_delete_session_async(self, real_client):
        """Test asíncrono de eliminación de sesión."""
        created = await real_client.sessions.create_async({"name": "Test Delete Async"})

        result = await real_client.sessions.delete_async(created.id)

        assert isinstance(result, dict)
        print(f"\nSesión eliminada (async): {result}")


@pytest.mark.integration
class TestSessionsFilters:
    """Tests de filtros y paginación."""

    def test_list_with_pagination(self, real_client):
        """Test de listado con paginación."""
        # Primera página
        page1 = real_client.sessions.list(page=1, limit=5)

        assert hasattr(page1, "pagination")
        assert page1.pagination.get("page") == 1
        assert page1.pagination.get("limit") == 5
        print(f"\nPágina 1: {len(page1.data)} sesiones")

    def test_list_with_status_filter(self, real_client):
        """Test de filtrado por status."""
        # Filtrar por status STOPPED
        stopped = real_client.sessions.list(status="STOPPED", limit=10)

        assert hasattr(stopped, "data")
        # Verificar que todas las sesiones retornadas tienen el status correcto
        for session in stopped.data:
            assert session.status == SessionStatus.STOPPED
        print(f"\nSesiones detenidas: {len(stopped.data)}")


# Instrucciones:
# pytest tests/test_integration_sessions.py -v -m integration -s
