"""
Tests para los endpoints de logs.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from app.routes.logs import get_logs


@pytest.mark.asyncio
async def test_get_logs_success(mock_supplier_admin_user, mock_db_pool):
    """Test de listado de logs exitoso."""
    pool, conn = mock_db_pool
    
    logs_data = [
        {"hora": "12:00:00", "fecha": "2025-01-15", "usuario": 1},
        {"hora": "13:00:00", "fecha": "2025-01-15", "usuario": 2}
    ]
    
    from tests.conftest import create_mock_record
    mock_rows = [create_mock_record({"fn_get_logs": json.dumps(log)}) for log in logs_data]
    conn.fetch = AsyncMock(return_value=mock_rows)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.logs.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_logs(
            empresa=1,
            usuario=None,
            fecha_desde=None,
            fecha_hasta=None,
            limit=10,
            offset=0,
            current_user=mock_supplier_admin_user
        )
        
        assert result.status_code == 200
        data = json.loads(result.body)
        assert len(data) == 2


@pytest.mark.asyncio
async def test_get_logs_with_filters(mock_supplier_admin_user, mock_db_pool):
    """Test de listado de logs con filtros."""
    pool, conn = mock_db_pool
    
    logs_data = [
        {"hora": "12:00:00", "fecha": "2025-01-15", "usuario": 1}
    ]
    
    from tests.conftest import create_mock_record
    mock_rows = [create_mock_record({"fn_get_logs": json.dumps(log)}) for log in logs_data]
    conn.fetch = AsyncMock(return_value=mock_rows)
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.logs.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_logs(
            empresa=1,
            usuario=1,
            fecha_desde="2025-01-01",
            fecha_hasta="2025-01-31",
            limit=10,
            offset=0,
            current_user=mock_supplier_admin_user
        )
        
        assert result.status_code == 200
        data = json.loads(result.body)
        assert len(data) == 1


@pytest.mark.asyncio
async def test_get_logs_empty(mock_supplier_admin_user, mock_db_pool):
    """Test de listado de logs vacío."""
    pool, conn = mock_db_pool
    
    conn.fetch = AsyncMock(return_value=[])
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.logs.get_pool", new_callable=AsyncMock, return_value=pool):
        result = await get_logs(
            empresa=1,
            usuario=None,
            fecha_desde=None,
            fecha_hasta=None,
            limit=10,
            offset=0,
            current_user=mock_supplier_admin_user
        )
        
        assert result.status_code == 200
        data = json.loads(result.body)
        assert len(data) == 0


@pytest.mark.asyncio
async def test_get_logs_error(mock_supplier_admin_user, mock_db_pool):
    """Test de listado de logs con error."""
    pool, conn = mock_db_pool
    
    conn.fetch = AsyncMock(side_effect=Exception("Error en BD"))
    
    # Patch get_pool usando AsyncMock con return_value
    with patch("app.routes.logs.get_pool", new_callable=AsyncMock, return_value=pool):
        with pytest.raises(HTTPException) as exc_info:
            await get_logs(
                empresa=1,
                usuario=None,
                fecha_desde=None,
                fecha_hasta=None,
                limit=10,
                offset=0,
                current_user=mock_supplier_admin_user
            )
        
        assert exc_info.value.status_code == 500

