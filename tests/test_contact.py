"""
Tests para los endpoints de contacto.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.contact import notify_supplier, get_supplier_contact


@pytest.mark.asyncio
async def test_get_supplier_contact_success(mock_db_pool):
    """Test de obtención de contacto de proveedor exitosa."""
    pool, conn = mock_db_pool
    
    contact_data = {
        "userId": 1,
        "userFullName": "John Doe",
        "companyName": "Acme Corp",
        "companyId": 1,
        "userMail": "john@example.com",
        "supplierMail": "supplier@example.com",
        "hasSentMail": False
    }
    
    mock_row = MagicMock()
    mock_row.__getitem__.return_value = json.dumps(contact_data)
    conn.fetchrow = AsyncMock(return_value=mock_row)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.contact.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_supplier_contact("test_user")
        
        assert result["userId"] == 1
        assert result["userFullName"] == "John Doe"


@pytest.mark.asyncio
async def test_get_supplier_contact_not_found(mock_db_pool):
    """Test de obtención de contacto de proveedor no encontrado."""
    pool, conn = mock_db_pool
    
    mock_row = MagicMock()
    mock_row.__getitem__.return_value = None
    conn.fetchrow = AsyncMock(return_value=mock_row)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.contact.get_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(HTTPException) as exc_info:
            await get_supplier_contact("nonexistent")
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_notify_supplier_success(mock_db_pool):
    """Test de notificación a proveedor exitosa."""
    pool, conn = mock_db_pool
    
    contact_data = {
        "userId": 1,
        "userFullName": "John Doe",
        "companyName": "Acme Corp",
        "companyId": 1,
        "userMail": "john@example.com",
        "supplierMail": "supplier@example.com",
        "hasSentMail": False
    }
    
    mock_row = MagicMock()
    mock_row.__getitem__.return_value = json.dumps(contact_data)
    conn.fetchrow = AsyncMock(return_value=mock_row)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.contact.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.contact.get_supplier_contact", return_value=contact_data):
            with patch("app.routes.contact.send_email_via_smtp", return_value=None):
                with patch("app.routes.contact.update_sent_mail", return_value=None):
                    from app.routes.contact import notify_supplier
                    result = await notify_supplier(username="test_user")
                    
                    assert "Correo enviado correctamente" in result["message"]


@pytest.mark.asyncio
async def test_notify_supplier_already_sent(mock_db_pool):
    """Test de notificación cuando ya se envió correo."""
    pool, conn = mock_db_pool
    
    contact_data = {
        "userId": 1,
        "userFullName": "John Doe",
        "companyName": "Acme Corp",
        "companyId": 1,
        "userMail": "john@example.com",
        "supplierMail": "supplier@example.com",
        "hasSentMail": True
    }
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.contact.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.contact.get_supplier_contact", return_value=contact_data):
            from app.routes.contact import notify_supplier
            result = await notify_supplier(username="test_user")
            
            assert "ya envió un correo" in result["message"].lower()


@pytest.mark.asyncio
async def test_notify_supplier_error(mock_db_pool):
    """Test de notificación con error."""
    pool, conn = mock_db_pool
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.contact.get_pool", new_callable=AsyncMock, return_value=pool):
        with patch("app.routes.contact.get_supplier_contact", side_effect=Exception("Error")):
            from app.routes.contact import notify_supplier
            with pytest.raises(HTTPException) as exc_info:
                await notify_supplier(username="test_user")
            
            assert exc_info.value.status_code == 500

