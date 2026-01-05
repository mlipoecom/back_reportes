"""
Tests para los endpoints de cambio de contraseña.
"""
import pytest
import bcrypt
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.change_password import change_password


@pytest.mark.asyncio
async def test_change_password_success(mock_supplier_admin_user, mock_user_data, mock_db_pool):
    """Test de cambio de contraseña exitoso."""
    pool, conn = mock_db_pool
    
    user_data = mock_user_data.copy()
    user_data["status"] = "activo"
    user_data["entityStatus"] = "activo"
    
    conn.fetchval = AsyncMock(return_value="OK")
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.change_password.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.change_password.get_user_by_username", return_value=user_data):
            with patch("app.routes.change_password.send_new_password_email", return_value=None):
                result = await change_password("test_user", mock_supplier_admin_user)
                
                assert result["ejecutado"] is True
                assert "exitosamente" in result["info"].lower()


@pytest.mark.asyncio
async def test_change_password_user_not_found(mock_supplier_admin_user, mock_db_pool):
    """Test de cambio de contraseña con usuario no encontrado."""
    pool, conn = mock_db_pool
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.change_password.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.change_password.get_user_by_username", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await change_password("nonexistent", mock_supplier_admin_user)
            
            assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_change_password_user_inactive(mock_supplier_admin_user, mock_user_data, mock_db_pool):
    """Test de cambio de contraseña con usuario inactivo."""
    pool, conn = mock_db_pool
    
    user_data = mock_user_data.copy()
    user_data["status"] = "inactivo"
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.change_password.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.change_password.get_user_by_username", return_value=user_data):
            with pytest.raises(HTTPException) as exc_info:
                await change_password("test_user", mock_supplier_admin_user)
            
            assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_change_password_entity_inactive(mock_supplier_admin_user, mock_user_data, mock_db_pool):
    """Test de cambio de contraseña con entidad inactiva."""
    pool, conn = mock_db_pool
    
    user_data = mock_user_data.copy()
    user_data["entityStatus"] = "inactivo"
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.change_password.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.change_password.get_user_by_username", return_value=user_data):
            with pytest.raises(HTTPException) as exc_info:
                await change_password("test_user", mock_supplier_admin_user)
            
            assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_change_password_db_error(mock_supplier_admin_user, mock_user_data, mock_db_pool):
    """Test de cambio de contraseña con error en BD."""
    pool, conn = mock_db_pool
    
    user_data = mock_user_data.copy()
    user_data["status"] = "activo"
    user_data["entityStatus"] = "activo"
    
    conn.fetchval = AsyncMock(return_value="Error en BD")
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.change_password.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.change_password.get_user_by_username", return_value=user_data):
            result = await change_password("test_user", mock_supplier_admin_user)
            
            assert result["ejecutado"] is False


@pytest.mark.asyncio
async def test_change_password_email_failure(mock_supplier_admin_user, mock_user_data, mock_db_pool):
    """Test de cambio de contraseña con fallo en envío de email."""
    pool, conn = mock_db_pool
    
    user_data = mock_user_data.copy()
    user_data["status"] = "activo"
    user_data["entityStatus"] = "activo"
    
    conn.fetchval = AsyncMock(return_value="OK")
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.change_password.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.change_password.get_user_by_username", return_value=user_data):
            with patch("app.routes.change_password.send_new_password_email", side_effect=Exception("SMTP Error")):
                from fastapi.responses import JSONResponse
                result = await change_password("test_user", mock_supplier_admin_user)
                
                assert result.status_code == 500
                assert "no se pudo enviar el correo" in result.body.decode().lower()

