"""
Tests para los endpoints de actualización de estado.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.update_status import update_status


@pytest.mark.asyncio
async def test_update_status_success(mock_supplier_admin_user, mock_db_pool):
    """Test de actualización de estado exitosa."""
    pool, conn = mock_db_pool
    
    conn.fetchval = AsyncMock(return_value="OK")
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.update_status.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await update_status(
            p_id=1,
            p_entity="user",
            p_status="activo",
            authorization="Bearer token123",
            current_user=mock_supplier_admin_user
        )
        
        assert result["ejecutado"] is True
        assert "actualización exitosa" in result["info"].lower()


@pytest.mark.asyncio
async def test_update_status_failure(mock_supplier_admin_user, mock_db_pool):
    """Test de actualización de estado fallida."""
    pool, conn = mock_db_pool
    
    conn.fetchval = AsyncMock(return_value="Error: Entidad no encontrada")
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.update_status.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await update_status(
            p_id=999,
            p_entity="user",
            p_status="activo",
            authorization="Bearer token123",
            current_user=mock_supplier_admin_user
        )
        
        assert result["ejecutado"] is False
        assert "error" in result["info"].lower() or "no encontrada" in result["info"].lower()


@pytest.mark.asyncio
async def test_update_status_invalid_token(mock_supplier_admin_user, mock_db_pool):
    """Test de actualización de estado con token inválido."""
    pool, conn = mock_db_pool
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.update_status.get_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(HTTPException) as exc_info:
            await update_status(
                p_id=1,
                p_entity="user",
                p_status="activo",
                authorization="Invalid token",
                current_user=mock_supplier_admin_user
            )
        
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_update_status_missing_token(mock_supplier_admin_user, mock_db_pool):
    """Test de actualización de estado sin token."""
    pool, conn = mock_db_pool
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.update_status.get_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(HTTPException) as exc_info:
            await update_status(
                p_id=1,
                p_entity="user",
                p_status="activo",
                authorization=None,
                current_user=mock_supplier_admin_user
            )
        
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_update_status_different_entities(mock_supplier_admin_user, mock_db_pool):
    """Test de actualización de estado para diferentes entidades."""
    pool, conn = mock_db_pool
    
    conn.fetchval = AsyncMock(return_value="OK")
    
    entities = ["company", "user", "supplier", "customer"]
    statuses = ["activo", "suspendido", "inactivo"]
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.update_status.get_pool", new_callable=AsyncMock, return_value=pool):
        for entity in entities:
            for status in statuses:
                result = await update_status(
                    p_id=1,
                    p_entity=entity,
                    p_status=status,
                    authorization="Bearer token123",
                    current_user=mock_supplier_admin_user
                )
                
                assert result["ejecutado"] is True


@pytest.mark.asyncio
async def test_update_status_db_error(mock_supplier_admin_user, mock_db_pool):
    """Test de actualización de estado con error en BD."""
    pool, conn = mock_db_pool
    
    conn.fetchval = AsyncMock(side_effect=Exception("Error en BD"))
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.update_status.get_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(HTTPException) as exc_info:
            await update_status(
                p_id=1,
                p_entity="user",
                p_status="activo",
                authorization="Bearer token123",
                current_user=mock_supplier_admin_user
            )
        
        assert exc_info.value.status_code == 500

